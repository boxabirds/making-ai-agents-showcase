"""
Citation parsing and verification.

Citation format: [path:start_line-end_line]
Example: [lib/core/Axios.js:10-25]
"""

import re
from dataclasses import dataclass
from typing import Optional

from tech_writer.store import CacheStore


# Citation pattern: [path:start-end]
CITATION_PATTERN = re.compile(r'\[([^:\]]+):(\d+)-(\d+)\]')


@dataclass
class Citation:
    """A parsed citation."""
    path: str
    start_line: int
    end_line: int


@dataclass
class VerificationResult:
    """Result of verifying a citation."""
    citation: Citation
    valid: bool
    content: Optional[str] = None
    error: Optional[str] = None


def parse_citation(citation_str: str) -> Citation:
    """
    Parse a citation string.

    Args:
        citation_str: Citation in format "path:start-end"

    Returns:
        Citation object

    Raises:
        ValueError: If format is invalid
    """
    # Handle both with and without brackets
    citation_str = citation_str.strip("[]")

    # Try to parse with pattern
    parts = citation_str.rsplit(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid citation format: missing colon in '{citation_str}'")

    path = parts[0]
    line_range = parts[1]

    # Parse line range
    range_parts = line_range.split("-")
    if len(range_parts) != 2:
        raise ValueError(f"Invalid citation format: expected 'start-end' in '{citation_str}'")

    try:
        start_line = int(range_parts[0])
        end_line = int(range_parts[1])
    except ValueError:
        raise ValueError(f"Invalid citation format: non-numeric line numbers in '{citation_str}'")

    if start_line <= 0 or end_line <= 0:
        raise ValueError(f"Invalid citation format: line numbers must be positive in '{citation_str}'")

    if start_line > end_line:
        raise ValueError(f"Invalid citation format: start_line > end_line in '{citation_str}'")

    return Citation(path=path, start_line=start_line, end_line=end_line)


def extract_citations(markdown: str) -> list[Citation]:
    """
    Extract all citations from markdown.

    Args:
        markdown: Markdown content

    Returns:
        List of Citation objects
    """
    citations = []

    for match in CITATION_PATTERN.finditer(markdown):
        path = match.group(1)
        start_line = int(match.group(2))
        end_line = int(match.group(3))

        citations.append(Citation(
            path=path,
            start_line=start_line,
            end_line=end_line,
        ))

    return citations


def verify_citation(
    citation: Citation,
    store: CacheStore,
) -> VerificationResult:
    """
    Verify a citation against cached content.

    Args:
        citation: Citation to verify
        store: Cache store

    Returns:
        VerificationResult with validity and content/error
    """
    # Check if file is cached
    cached = store.get_file(citation.path)
    if cached is None:
        return VerificationResult(
            citation=citation,
            valid=False,
            error=f"File not found in cache: {citation.path}",
        )

    # Check line range
    lines = cached.content.splitlines()
    total_lines = len(lines)

    if citation.start_line > total_lines:
        return VerificationResult(
            citation=citation,
            valid=False,
            error=f"Start line {citation.start_line} out of range (file has {total_lines} lines)",
        )

    if citation.end_line > total_lines:
        return VerificationResult(
            citation=citation,
            valid=False,
            error=f"End line {citation.end_line} out of range (file has {total_lines} lines)",
        )

    # Extract cited content
    start_idx = citation.start_line - 1  # 0-indexed
    end_idx = citation.end_line  # exclusive end for slice

    cited_lines = lines[start_idx:end_idx]
    content = "\n".join(cited_lines)

    return VerificationResult(
        citation=citation,
        valid=True,
        content=content,
    )


def verify_all_citations(
    markdown: str,
    store: CacheStore,
) -> tuple[list[VerificationResult], int, int]:
    """
    Verify all citations in a document.

    Args:
        markdown: Markdown content
        store: Cache store

    Returns:
        Tuple of (results, valid_count, invalid_count)
    """
    citations = extract_citations(markdown)
    results = []
    valid_count = 0
    invalid_count = 0

    for citation in citations:
        result = verify_citation(citation, store)
        results.append(result)

        if result.valid:
            valid_count += 1
        else:
            invalid_count += 1

    return results, valid_count, invalid_count


def format_citation(path: str, start_line: int, end_line: int) -> str:
    """
    Format a citation string.

    Args:
        path: File path
        start_line: Start line (1-indexed)
        end_line: End line (inclusive)

    Returns:
        Citation string in format [path:start-end]
    """
    return f"[{path}:{start_line}-{end_line}]"
