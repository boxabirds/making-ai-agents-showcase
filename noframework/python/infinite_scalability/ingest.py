import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

from binaryornot.check import is_binary

from common.logging import logger
from common.utils import get_gitignore_spec
from .models import ChunkRecord, FileRecord, SymbolRecord, EdgeRecord
from .parser import extract_code_chunks, extract_symbols, extract_imports, extract_edges, supports_lang
from .store import Store


def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def detect_lang(path: Path) -> str:
    """
    Map extensions to tree-sitter language keys and prefer only supported languages.
    """
    from .parser import TS_LANGS

    ext = path.suffix.lower()
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".md": "markdown",
        ".markdown": "markdown",
        ".json": "json",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".cc": "cpp",
        ".cpp": "cpp",
        ".c": "c",
        ".cs": "c_sharp",
        ".rb": "ruby",
        ".php": "php",
    }
    lang = ext_map.get(ext, ext.lstrip(".") or "unknown")
    return lang if lang in TS_LANGS else "unknown"


def chunk_text_lines(text: str) -> Tuple[int, List[Tuple[int, int, str, str]]]:
    """
    Simple chunker: for markdown/text split on blank lines; otherwise single chunk for whole file.
    Returns total lines and list of (start, end, chunk_text).
    """
    lines = text.splitlines()
    total = len(lines)
    if total == 0:
        return 0, []

    # Markdown/plaintext chunk by paragraphs
    chunks: List[Tuple[int, int, str, str]] = []
    start = 1
    if "\n\n" in text or any(l.strip() == "" for l in lines):
        buf: List[str] = []
        current_start = 1
        for idx, line in enumerate(lines, start=1):
            if line.strip() == "":
                if buf:
                    chunks.append((current_start, idx - 1, "\n".join(buf), "paragraph"))
                    buf = []
                current_start = idx + 1
            else:
                if not buf:
                    current_start = idx
                buf.append(line)
        if buf:
            chunks.append((current_start, total, "\n".join(buf), "paragraph"))
    else:
        chunks.append((1, total, text, "block"))

    return total, chunks


def walk_files(root: Path, respect_gitignore: bool = True) -> Iterable[Path]:
    spec = get_gitignore_spec(str(root)) if respect_gitignore else None
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if not respect_gitignore:
            yield path
            continue
        rel = path.relative_to(root).as_posix()
        if spec and spec.match_file(rel):
            continue
        yield path


def ingest_repo(root: Path, store: Store, respect_gitignore: bool = True) -> None:
    """
    Minimal ingestion: walk files, hash, chunk text, and persist file/chunk records.
    """
    max_files = int(os.environ.get("INGEST_FILE_LIMIT", "0"))
    processed = 0
    for path in walk_files(root, respect_gitignore=respect_gitignore):
        if is_binary(str(path)):
            continue
        if max_files and processed >= max_files:
            break
        content_bytes = path.read_bytes()
        digest = file_hash(content_bytes)
        stat = path.stat()
        lang = detect_lang(path)
        file_rec = FileRecord(
            path=str(path),
            hash=digest,
            lang=lang,
            size=stat.st_size,
            mtime=datetime.fromtimestamp(stat.st_mtime),
            parsed=supports_lang(lang),
        )
        file_id = store.add_file(file_rec)

        text = content_bytes.decode("utf-8", errors="replace")
        total_lines = len(text.splitlines())

        chunk_specs: List[Tuple[int, int, str, str]] = []
        symbol_specs: List[Tuple[str, str, int, int]] = []
        if supports_lang(file_rec.lang):
            chunk_specs = extract_code_chunks(text, file_rec.lang)
            symbol_specs = extract_symbols(text, file_rec.lang)
        else:
            logger.warning("Unsupported language for tree-sitter parsing; skipping: %s (%s)", file_rec.lang, path)
            continue

        if not chunk_specs and total_lines == 0:
            continue

        chunk_records: List[ChunkRecord] = []
        embeddings_payload = []
        for start, end, chunk_text, kind in chunk_specs or [(1, total_lines or 1, text, "block")]:
            chunk_records.append(
                ChunkRecord(
                    file_id=file_id,
                    start_line=start,
                    end_line=end,
                    kind=kind,
                    text=chunk_text,
                    hash=file_hash(chunk_text.encode("utf-8")),
                )
            )
            # deterministic embedding: hash to 8-d float vector
            h = hashlib.sha256(chunk_text.encode("utf-8")).digest()
            vec = []
            for i in range(8):
                seg = h[i * 4 : (i + 1) * 4]
                val = int.from_bytes(seg, "little", signed=False) / 2**32
                vec.append(val)
            import numpy as np
            vec_arr = np.array(vec, dtype=np.float32)
            embeddings_payload.append((None, vec_arr.tobytes(), vec_arr.shape[0]))
        chunk_ids = store.add_chunks(chunk_records)
        # store embeddings aligned by chunk ids
        if embeddings_payload and chunk_ids:
            ready = []
            for cid, payload in zip(chunk_ids, embeddings_payload):
                ready.append((cid, payload[1], payload[2]))
            store.add_chunk_embeddings(ready)
        processed += 1

        # symbols
        symbol_records: List[SymbolRecord] = []
        for name, kind, start_line, end_line in symbol_specs:
            symbol_records.append(
                SymbolRecord(
                    file_id=file_id,
                    name=name,
                    kind=kind,
                    signature=None,
                    start_line=start_line,
                    end_line=end_line,
                    doc=None,
                    parent_symbol_id=None,
                )
            )
        # import symbols via tree-sitter
        import_symbols: List[SymbolRecord] = []
        if supports_lang(file_rec.lang):
            for mod, line_no in extract_imports(text, file_rec.lang):
                import_symbols.append(
                    SymbolRecord(
                        file_id=file_id,
                        name=mod,
                        kind="import",
                        signature=None,
                        start_line=line_no,
                        end_line=line_no,
                        doc=None,
                        parent_symbol_id=None,
                    )
                )
        if symbol_records or import_symbols:
            ids = store.add_symbols(symbol_records + import_symbols)
            name_to_id = {}
            for rec, sid in zip(symbol_records + import_symbols, ids):
                rec.id = sid
                name_to_id.setdefault(rec.name, sid)
            edges: List[EdgeRecord] = []
            if supports_lang(file_rec.lang):
                edge_specs = extract_edges(
                    text,
                    file_rec.lang,
                    [(s.name, s.kind, s.start_line, s.end_line) for s in symbol_records],
                )
                for src_name, dst_name, edge_type in edge_specs:
                    src_id = name_to_id.get(src_name)
                    dst_id = name_to_id.get(dst_name)
                    if src_id and dst_id:
                        edges.append(EdgeRecord(src_symbol_id=src_id, dst_symbol_id=dst_id, edge_type=edge_type))
            # import edges from defs/classes to imports
            for sym in symbol_records:
                if sym.id is None:
                    continue
                for imp in import_symbols:
                    if imp.id is None:
                        continue
                    edges.append(
                        EdgeRecord(
                            src_symbol_id=sym.id,
                            dst_symbol_id=imp.id,
                            edge_type=f"imports:{imp.name}",
                        )
                    )
            if edges:
                store.add_edges(edges)
import os
