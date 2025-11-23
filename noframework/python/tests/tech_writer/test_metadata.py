"""Unit tests for metadata module."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tech_writer.metadata import (
    METADATA_VERSION,
    CitationStats,
    CostInfo,
    InvalidCitation,
    RunMetadata,
    create_metadata,
)


class TestRunMetadata:
    """Tests for RunMetadata dataclass."""

    def test_to_dict_includes_required_fields(self):
        """All required fields are present in output."""
        metadata = RunMetadata(
            version="1.0",
            model="gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
            timestamp="2025-01-15T10:30:00+00:00",
            output_file="report.md",
        )
        result = metadata.to_dict()

        assert result["version"] == "1.0"
        assert result["model"] == "gpt-4"
        assert result["repo_path"] == "/path/to/repo"
        assert result["prompt_file"] == "prompt.txt"
        assert result["timestamp"] == "2025-01-15T10:30:00+00:00"
        assert result["output_file"] == "report.md"

    def test_to_dict_excludes_none_values(self):
        """Optional fields with None values are excluded."""
        metadata = RunMetadata(
            version="1.0",
            model="gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
            timestamp="2025-01-15T10:30:00+00:00",
            output_file="report.md",
            citations=None,
            cost=None,
        )
        result = metadata.to_dict()

        assert "citations" not in result
        assert "cost" not in result

    def test_to_dict_includes_citations_when_present(self):
        """Citations are included when provided."""
        citation_stats = CitationStats(
            total=10,
            valid=8,
            invalid=2,
            invalid_citations=[
                InvalidCitation(
                    path="src/main.py",
                    start_line=100,
                    end_line=105,
                    error="Line range exceeds file length",
                )
            ],
        )
        metadata = RunMetadata(
            version="1.0",
            model="gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
            timestamp="2025-01-15T10:30:00+00:00",
            output_file="report.md",
            citations=citation_stats,
        )
        result = metadata.to_dict()

        assert "citations" in result
        assert result["citations"]["total"] == 10
        assert result["citations"]["valid"] == 8
        assert result["citations"]["invalid"] == 2
        assert len(result["citations"]["invalid_citations"]) == 1

    def test_to_dict_includes_cost_when_present(self):
        """Cost info is included when provided."""
        cost_info = CostInfo(
            total_cost_usd=0.0123,
            total_tokens=5000,
            total_calls=3,
            provider="openrouter",
            model="anthropic/claude-3-sonnet",
        )
        metadata = RunMetadata(
            version="1.0",
            model="anthropic/claude-3-sonnet",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
            timestamp="2025-01-15T10:30:00+00:00",
            output_file="report.md",
            cost=cost_info,
        )
        result = metadata.to_dict()

        assert "cost" in result
        assert result["cost"]["total_cost_usd"] == 0.0123
        assert result["cost"]["total_tokens"] == 5000
        assert result["cost"]["total_calls"] == 3
        assert result["cost"]["provider"] == "openrouter"


class TestCreateMetadata:
    """Tests for create_metadata function."""

    def test_creates_metadata_file(self, tmp_path: Path):
        """Metadata file is created alongside output."""
        output_file = tmp_path / "report.md"
        output_file.write_text("# Report")

        metadata_path = create_metadata(
            output_file=output_file,
            model="gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
        )

        assert metadata_path.exists()
        assert metadata_path.name == "report.metadata.json"
        assert metadata_path.parent == tmp_path

    def test_metadata_file_contains_valid_json(self, tmp_path: Path):
        """Metadata file contains valid JSON."""
        output_file = tmp_path / "report.md"
        output_file.write_text("# Report")

        metadata_path = create_metadata(
            output_file=output_file,
            model="gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
        )

        content = metadata_path.read_text()
        data = json.loads(content)  # Should not raise

        assert isinstance(data, dict)

    def test_metadata_contains_required_fields(self, tmp_path: Path):
        """Metadata file contains all required fields."""
        output_file = tmp_path / "report.md"
        output_file.write_text("# Report")

        metadata_path = create_metadata(
            output_file=output_file,
            model="gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
        )

        data = json.loads(metadata_path.read_text())

        assert data["version"] == METADATA_VERSION
        assert data["model"] == "gpt-4"
        assert data["repo_path"] == "/path/to/repo"
        assert data["prompt_file"] == "prompt.txt"
        assert data["output_file"] == str(output_file)
        assert "timestamp" in data

    def test_timestamp_is_iso8601(self, tmp_path: Path):
        """Timestamp is valid ISO 8601 format."""
        output_file = tmp_path / "report.md"
        output_file.write_text("# Report")

        metadata_path = create_metadata(
            output_file=output_file,
            model="gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
        )

        data = json.loads(metadata_path.read_text())
        timestamp = data["timestamp"]

        # Should parse without error
        parsed = datetime.fromisoformat(timestamp)
        assert parsed.tzinfo is not None  # Should have timezone

    def test_citation_stats_included_when_provided(self, tmp_path: Path):
        """Citation stats are included in metadata when provided."""
        output_file = tmp_path / "report.md"
        output_file.write_text("# Report")

        citation_stats = CitationStats(
            total=5,
            valid=4,
            invalid=1,
            invalid_citations=[
                InvalidCitation(
                    path="src/util.py",
                    start_line=50,
                    end_line=55,
                    error="File not found",
                )
            ],
        )

        metadata_path = create_metadata(
            output_file=output_file,
            model="gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
            citations=citation_stats,
        )

        data = json.loads(metadata_path.read_text())

        assert "citations" in data
        assert data["citations"]["total"] == 5
        assert data["citations"]["valid"] == 4
        assert data["citations"]["invalid"] == 1
        assert len(data["citations"]["invalid_citations"]) == 1
        assert data["citations"]["invalid_citations"][0]["path"] == "src/util.py"

    def test_cost_info_included_when_provided(self, tmp_path: Path):
        """Cost info is included in metadata when provided."""
        output_file = tmp_path / "report.md"
        output_file.write_text("# Report")

        cost_info = CostInfo(
            total_cost_usd=0.05,
            total_tokens=10000,
            total_calls=5,
            provider="openrouter",
            model="openai/gpt-4",
        )

        metadata_path = create_metadata(
            output_file=output_file,
            model="openai/gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
            cost=cost_info,
        )

        data = json.loads(metadata_path.read_text())

        assert "cost" in data
        assert data["cost"]["total_cost_usd"] == 0.05
        assert data["cost"]["total_tokens"] == 10000
        assert data["cost"]["total_calls"] == 5
        assert data["cost"]["provider"] == "openrouter"

    def test_handles_nested_output_path(self, tmp_path: Path):
        """Metadata file created in nested directory."""
        nested_dir = tmp_path / "reports" / "2025"
        nested_dir.mkdir(parents=True)
        output_file = nested_dir / "report.md"
        output_file.write_text("# Report")

        metadata_path = create_metadata(
            output_file=output_file,
            model="gpt-4",
            repo_path="/path/to/repo",
            prompt_file="prompt.txt",
        )

        assert metadata_path.exists()
        assert metadata_path.parent == nested_dir


class TestInvalidCitation:
    """Tests for InvalidCitation dataclass."""

    def test_fields(self):
        """InvalidCitation has expected fields."""
        citation = InvalidCitation(
            path="src/main.py",
            start_line=10,
            end_line=20,
            error="Line range invalid",
        )

        assert citation.path == "src/main.py"
        assert citation.start_line == 10
        assert citation.end_line == 20
        assert citation.error == "Line range invalid"


class TestCitationStats:
    """Tests for CitationStats dataclass."""

    def test_fields(self):
        """CitationStats has expected fields."""
        stats = CitationStats(
            total=100,
            valid=95,
            invalid=5,
            invalid_citations=[],
        )

        assert stats.total == 100
        assert stats.valid == 95
        assert stats.invalid == 5
        assert stats.invalid_citations == []


class TestCostInfo:
    """Tests for CostInfo dataclass."""

    def test_fields(self):
        """CostInfo has expected fields."""
        cost = CostInfo(
            total_cost_usd=0.123,
            total_tokens=50000,
            total_calls=10,
            provider="openrouter",
            model="anthropic/claude-3-opus",
        )

        assert cost.total_cost_usd == 0.123
        assert cost.total_tokens == 50000
        assert cost.total_calls == 10
        assert cost.provider == "openrouter"
        assert cost.model == "anthropic/claude-3-opus"
