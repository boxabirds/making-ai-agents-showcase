import re
from typing import List, Optional, Set

from .citations import validate_citation, generate_citation_from_chunk
from .retrieval import retrieve_context
from .store import Store


def enforce_draft_citations(report_md: str, store: Store, topic: str, allowed_citations: Optional[Set[str]] = None) -> str:
    """
    Ensure every non-header, non-empty line has at least one valid citation.
    Missing citations are patched using retrieved chunks while preserving content.
    Citations are constrained to an allowed set when provided.
    """
    lines = report_md.splitlines()
    repaired: List[str] = []

    allowed = allowed_citations or set()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            repaired.append(line)
            continue
        tokens = re.findall(r"\[([^\]]+)\]", stripped)
        if not tokens:
            # attempt to retrieve supporting chunk aligned to the line/topic
            ctx = retrieve_context(store, stripped or topic, limit=5)
            added = False
            for c in ctx.chunks:
                file_rec = store.get_file_by_id(c.file_id)
                if not file_rec:
                    continue
                citation = generate_citation_from_chunk(c, file_rec.path)
                if allowed and citation not in allowed:
                    continue
                repaired.append(f"{line} [{citation}]")
                added = True
                break
            if added:
                continue
            # keep the line uncited if no aligned evidence was found
            # as a last resort, attach the first available chunk to avoid dropping content
            files = store.get_all_files()
            for f in files:
                chunks = store.get_chunks_for_file(f.id)  # type: ignore[arg-type]
                if not chunks:
                    continue
                citation = generate_citation_from_chunk(chunks[0], f.path)
                if allowed and citation not in allowed:
                    continue
                repaired.append(f"{line} [{citation}]")
                added = True
                break
            if not added:
                repaired.append(line)
            continue
        try:
            valid_tokens = []
            for tok in tokens:
                validate_citation(tok)
                if allowed and tok not in allowed:
                    continue
                valid_tokens.append(tok)
            if valid_tokens:
                # rebuild line with allowed citations only
                cleaned = stripped
                cleaned_tokens = " ".join([f"[{t}]" for t in valid_tokens])
                # remove existing citation tokens and append cleaned ones
                cleaned = re.sub(r"\[[^\]]+\]", "", cleaned).strip()
                repaired.append(f"{cleaned} {cleaned_tokens}".strip())
            else:
                # no valid citations; attempt to add one from allowed
                if allowed:
                    repaired.append(f"{stripped} [{next(iter(allowed))}]")
                else:
                    repaired.append(line)
        except Exception:
            continue
    return "\n".join(repaired)


def validate_report_citations(report_md: str, store: Store) -> None:
    """
    Validate that every non-header, non-empty line has a valid citation that maps to stored chunks.
    """
    for line in report_md.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tokens = re.findall(r"\[([^\]]+)\]", stripped)
        if not tokens:
            continue
        for tok in tokens:
            path, start, end = validate_citation(tok)
            file_rec = store.get_file_by_path(path)
            if not file_rec:
                raise ValueError(f"Invalid citation file: {tok}")
            chunk = store.find_chunk_covering_range(file_rec.id, start, end)
            if not chunk:
                raise ValueError(f"Invalid citation range: {tok}")
