# Feature 2: V1-Compatible Metadata Output - Technical Design

## 1. Overview

Add metadata JSON output to tech_writer v2, providing v1 feature parity and enabling programmatic integration.

## 2. Metadata Schema

### 2.1 Base Schema

```python
@dataclass
class RunMetadata:
    """Metadata for a tech_writer run."""
    version: str = "1.0"  # Schema version for forward compatibility
    model: str
    repo_path: str
    prompt_file: str
    timestamp: str  # ISO 8601 format
    output_file: str
    citations: Optional[CitationStats] = None
    # Extended by Feature 1:
    cost: Optional[CostSummary] = None


@dataclass
class CitationStats:
    """Citation verification statistics."""
    total: int
    valid: int
    invalid: int
    invalid_citations: list[InvalidCitation]


@dataclass
class InvalidCitation:
    """Details of an invalid citation."""
    path: str
    start_line: int
    end_line: int
    error: str
```

### 2.2 Example Output

```json
{
  "version": "1.0",
  "model": "gpt-5.1",
  "repo_path": "/path/to/repo",
  "prompt_file": "prompts/architecture.txt",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "output_file": "report.md",
  "citations": {
    "total": 45,
    "valid": 42,
    "invalid": 3,
    "invalid_citations": [
      {
        "path": "src/main.py",
        "start_line": 100,
        "end_line": 105,
        "error": "Line range exceeds file length"
      }
    ]
  }
}
```

## 3. CLI Changes

### 3.1 New Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--metadata` | flag | False | Generate metadata JSON file |

### 3.2 Argument Definition

```python
parser.add_argument(
    "--metadata",
    action="store_true",
    help="Generate metadata JSON file alongside output (requires --output)",
)
```

### 3.3 Validation

```python
if args.metadata and not args.output:
    parser.error("--metadata requires --output")
```

## 4. Implementation

### 4.1 Metadata Generation Function

```python
# tech_writer/metadata.py

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

METADATA_VERSION = "1.0"


@dataclass
class InvalidCitation:
    path: str
    start_line: int
    end_line: int
    error: str


@dataclass
class CitationStats:
    total: int
    valid: int
    invalid: int
    invalid_citations: list[InvalidCitation]


@dataclass
class RunMetadata:
    version: str
    model: str
    repo_path: str
    prompt_file: str
    timestamp: str
    output_file: str
    citations: Optional[CitationStats] = None

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
) -> Path:
    """
    Create metadata JSON file alongside output.

    Args:
        output_file: Path to the output markdown file
        model: Model name used for generation
        repo_path: Path to the analyzed repository
        prompt_file: Path to the prompt file
        citations: Optional citation verification results

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
    )

    metadata_path = output_file.parent / f"{output_file.stem}.metadata.json"

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata.to_dict(), f, indent=2)

    return metadata_path
```

### 4.2 CLI Integration

```python
# In cli.py main()

# After report generation and citation verification...

if args.metadata:
    from tech_writer.metadata import create_metadata, CitationStats, InvalidCitation

    citation_stats = None
    if args.verify_citations:
        citation_stats = CitationStats(
            total=valid + invalid,
            valid=valid,
            invalid=invalid,
            invalid_citations=[
                InvalidCitation(
                    path=r.citation.path,
                    start_line=r.citation.start_line,
                    end_line=r.citation.end_line,
                    error=r.error,
                )
                for r in results if not r.valid
            ],
        )

    metadata_path = create_metadata(
        output_file=Path(args.output),
        model=args.model,
        repo_path=args.repo,
        prompt_file=args.prompt,
        citations=citation_stats,
    )
    print(f"Metadata written to: {metadata_path}", file=sys.stderr)
```

## 5. Extensibility

### 5.1 Cost Extension (Feature 1)

When Feature 1 (OpenRouter) is implemented, metadata will be extended:

```python
@dataclass
class RunMetadata:
    # ... existing fields ...
    cost: Optional[CostSummary] = None  # Added by Feature 1
```

The `create_metadata` function signature will add an optional `cost` parameter:

```python
def create_metadata(
    ...,
    cost: Optional[CostSummary] = None,
) -> Path:
```

### 5.2 Schema Versioning

The `version` field enables forward compatibility:
- `1.0`: Base schema (this feature)
- `1.1`: Add cost fields (Feature 1)

Consumers should check version and handle unknown fields gracefully.

## 6. File Structure

```
output/
├── report.md              # Generated report
└── report.metadata.json   # Metadata sidecar
```

## 7. Testing

### 7.1 Unit Tests

```python
class TestMetadata:
    def test_creates_metadata_file(self):
        """Metadata file created alongside output."""

    def test_metadata_contains_required_fields(self):
        """All required fields present in output."""

    def test_excludes_none_values(self):
        """Optional fields excluded when None."""

    def test_citation_stats_included(self):
        """Citation stats included when provided."""

    def test_timestamp_is_iso8601(self):
        """Timestamp is valid ISO 8601 format."""
```

### 7.2 CLI Tests

```python
class TestMetadataCLI:
    def test_metadata_requires_output(self):
        """--metadata without --output raises error."""

    def test_metadata_flag_creates_file(self):
        """--metadata creates .metadata.json file."""
```

### 7.3 BDD Feature

```gherkin
Feature: Metadata Output
  As a developer
  I want metadata about documentation runs
  So that I can track and integrate with CI/CD

  Scenario: Generate metadata file
    Given a repository and prompt file
    When I run tech_writer with --output report.md --metadata
    Then report.metadata.json should be created
    And it should contain model, repo_path, timestamp

  Scenario: Metadata includes citations
    Given a repository and prompt file
    When I run tech_writer with --output report.md --metadata --verify-citations
    Then report.metadata.json should contain citation stats

  Scenario: Metadata requires output flag
    When I run tech_writer with --metadata but no --output
    Then the command should fail with an error
```

## 8. File Changes Summary

| File | Changes |
|------|---------|
| `tech_writer/metadata.py` | New file: dataclasses and `create_metadata()` |
| `tech_writer/cli.py` | Add `--metadata` arg, call `create_metadata()` |
| `tests/tech_writer/test_metadata.py` | Unit tests |
| `tests/features/metadata.feature` | BDD tests |

## 9. Migration from V1

| V1 Field | V2 Field | Notes |
|----------|----------|-------|
| `model` | `model` | Same |
| `github_url` | `repo_path` | Now supports local paths |
| `repo_name` | - | Removed (derivable from repo_path) |
| `timestamp` | `timestamp` | Same format |
| `eval_output` | - | Out of scope for v2 |
| - | `version` | New: schema version |
| - | `prompt_file` | New: track prompt used |
| - | `output_file` | New: track output location |
| - | `citations` | New: citation stats |
