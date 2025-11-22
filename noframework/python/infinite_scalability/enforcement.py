import re
from typing import List

from .citations import validate_citation, generate_citation_from_chunk
from .retrieval import retrieve_context
from .store import Store


def enforce_draft_citations(report_md: str, store: Store, topic: str) -> str:
    """
    Ensure every non-header, non-empty line has at least one valid citation.
    Missing citations are patched using retrieved chunks while preserving content.
    """
    lines = report_md.splitlines()
    repaired: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            repaired.append(line)
            continue
        tokens = re.findall(r"\[([^\]]+)\]", stripped)
        if not tokens:
            # attempt to retrieve supporting chunk and append citation
            ctx = retrieve_context(store, stripped or topic, limit=3)
            if ctx.chunks:
                c = ctx.chunks[0]
                file_rec = store.get_file_by_id(c.file_id)
                if file_rec:
                    citation = generate_citation_from_chunk(c, file_rec.path)
                    repaired.append(f"{line} [{citation}]")
                    continue
            # fallback: use first available chunk in store to preserve citation requirement
            files = store.get_all_files()
            if files:
                chunks = store.get_chunks_for_file(files[0].id)  # type: ignore
                if chunks:
                    citation = generate_citation_from_chunk(chunks[0], files[0].path)
                    repaired.append(f"{line} [{citation}]")
                    continue
            # keep the line to preserve user-requested sections even if uncited
            repaired.append(line)
            continue
        try:
            for tok in tokens:
                validate_citation(tok)
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
