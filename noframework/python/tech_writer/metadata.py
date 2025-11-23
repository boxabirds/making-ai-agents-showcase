"""
Metadata output for tech_writer runs.

Provides V1-compatible metadata JSON output with:
- Run configuration (model, repo, prompt)
- Timestamp
- Citation verification stats
- Cost tracking (when OpenRouter is used)
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Schema version for forward compatibility
METADATA_VERSION = "1.0"


@dataclass
class InvalidCitation:
    """Details of an invalid citation."""

    path: str
    start_line: int
    end_line: int
    error: str


@dataclass
class CitationStats:
    """Citation verification statistics."""

    total: int
    valid: int
    invalid: int
    invalid_citations: list[InvalidCitation]


@dataclass
class CostInfo:
    """Cost information from LLM provider."""

    total_cost_usd: float
    total_tokens: int
    total_calls: int
    provider: str
    model: str


@dataclass
class RunMetadata:
    """Metadata for a tech_writer run."""

    version: str
    model: str
    repo_path: str
    prompt_file: str
    timestamp: str
    output_file: str
    citations: Optional[CitationStats] = None
    cost: Optional[CostInfo] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}


def create_metadata(
    output_file: Path,
    model: str,
    repo_path: str,
    prompt_file: str,
    citations: Optional[CitationStats] = None,
    cost: Optional[CostInfo] = None,
) -> Path:
    """
    Create metadata JSON file alongside output.

    Args:
        output_file: Path to the output markdown file
        model: Model name used for generation
        repo_path: Path to the analyzed repository
        prompt_file: Path to the prompt file
        citations: Optional citation verification results
        cost: Optional cost information from LLM provider

    Returns:
        Path to the created metadata file
    """
    metadata = RunMetadata(
        version=METADATA_VERSION,
        model=model,
        repo_path=str(repo_path),
        prompt_file=str(prompt_file),
        timestamp=datetime.now(timezone.utc).isoformat(),
        output_file=str(output_file),
        citations=citations,
        cost=cost,
    )

    metadata_path = output_file.parent / f"{output_file.stem}.metadata.json"

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata.to_dict(), f, indent=2)

    return metadata_path
