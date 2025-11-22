from typing import List, Tuple

from .models import ChunkRecord


def validate_citation(citation: str) -> Tuple[str, int, int]:
    """
    Parse citation in form path:start-end.
    """
    if ":" not in citation or "-" not in citation:
        raise ValueError("Invalid citation format")
    path, span = citation.split(":", 1)
    start_str, end_str = span.split("-")
    return path, int(start_str), int(end_str)


def format_citation(path: str, start: int, end: int) -> str:
    return f"{path}:{start}-{end}"


def generate_citation_from_chunk(chunk: ChunkRecord, path: str) -> str:
    return format_citation(path, chunk.start_line, chunk.end_line)
