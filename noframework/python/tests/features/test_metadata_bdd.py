"""
BDD-style feature tests for metadata output.

These tests implement the scenarios from the tech design:
- Generate metadata file with --metadata flag
- Metadata includes citation stats when --verify-citations used
- --metadata requires --output flag

Run with: pytest tests/features/test_metadata_bdd.py -v
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def simple_prompt_file(tmp_path):
    """Create a simple prompt file for testing."""
    prompt_file = tmp_path / "test_prompt.txt"
    prompt_file.write_text(
        "Write a brief 1-paragraph summary of what this codebase does. "
        "Focus only on the main purpose. Keep it under 100 words."
    )
    return prompt_file


@pytest.fixture
def test_repo():
    """Return path to the current repository for testing."""
    return Path(__file__).parent.parent.parent


class TestMetadataOutputFeature:
    """
    Feature: Metadata Output
      As a developer
      I want metadata about documentation runs
      So that I can track and integrate with CI/CD
    """

    @pytest.mark.integration
    def test_metadata_file_created_with_flag(self, simple_prompt_file, test_repo, tmp_path):
        """
        Scenario: Generate metadata file
          Given a repository and prompt file
          When I run tech_writer with --output report.md --metadata
          Then report.metadata.json should be created
          And it should contain model, repo_path, timestamp
        """
        output_file = tmp_path / "report.md"

        # Skip if no API key
        if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("No API key set (OPENROUTER_API_KEY or OPENAI_API_KEY)")

        # Determine provider based on available key
        if os.environ.get("OPENROUTER_API_KEY"):
            provider_args = ["--provider", "openrouter", "--model", "openai/gpt-4o-mini"]
        else:
            provider_args = ["--provider", "openai", "--model", "gpt-4o-mini"]

        # When: Run with --output and --metadata
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--output",
                str(output_file),
                "--metadata",
                "--max-exploration",
                "3",
                "--max-sections",
                "1",
            ]
            + provider_args,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Then: Command should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # And: report.metadata.json should be created
        metadata_file = tmp_path / "report.metadata.json"
        assert metadata_file.exists(), f"Metadata file not created. stderr: {result.stderr}"

        # And: It should contain required fields
        data = json.loads(metadata_file.read_text())
        assert "version" in data
        assert "model" in data
        assert "repo_path" in data
        assert "timestamp" in data
        assert "output_file" in data
        assert "prompt_file" in data

    @pytest.mark.integration
    def test_metadata_includes_citations_with_verify(
        self, simple_prompt_file, test_repo, tmp_path
    ):
        """
        Scenario: Metadata includes citations
          Given a repository and prompt file
          When I run tech_writer with --output report.md --metadata --verify-citations
          Then report.metadata.json should contain citation stats
        """
        output_file = tmp_path / "report.md"

        # Skip if no API key
        if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("No API key set (OPENROUTER_API_KEY or OPENAI_API_KEY)")

        # Determine provider based on available key
        if os.environ.get("OPENROUTER_API_KEY"):
            provider_args = ["--provider", "openrouter", "--model", "openai/gpt-4o-mini"]
        else:
            provider_args = ["--provider", "openai", "--model", "gpt-4o-mini"]

        # When: Run with --verify-citations
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--output",
                str(output_file),
                "--metadata",
                "--verify-citations",
                "--max-exploration",
                "3",
                "--max-sections",
                "1",
            ]
            + provider_args,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Then: Command should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # And: Metadata should contain citation stats
        metadata_file = tmp_path / "report.metadata.json"
        assert metadata_file.exists()

        data = json.loads(metadata_file.read_text())
        assert "citations" in data, f"No citations in metadata: {data}"
        assert "total" in data["citations"]
        assert "valid" in data["citations"]
        assert "invalid" in data["citations"]

    def test_metadata_requires_output_flag(self, simple_prompt_file, test_repo):
        """
        Scenario: Metadata requires output flag
          When I run tech_writer with --metadata but no --output
          Then the command should fail with an error
        """
        # When: Run with --metadata but no --output
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--metadata",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Then: Command should fail
        assert result.returncode != 0

        # And: Error message should mention --output
        assert "--metadata requires --output" in result.stderr

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get("OPENROUTER_API_KEY"),
        reason="OPENROUTER_API_KEY not set",
    )
    def test_metadata_includes_cost_with_openrouter(
        self, simple_prompt_file, test_repo, tmp_path
    ):
        """
        Scenario: Metadata includes cost when using OpenRouter
          Given I have an OpenRouter API key
          When I run tech_writer with --provider openrouter --output report.md --metadata
          Then report.metadata.json should contain cost information
        """
        output_file = tmp_path / "report.md"

        # When: Run with OpenRouter
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--output",
                str(output_file),
                "--metadata",
                "--provider",
                "openrouter",
                "--model",
                "openai/gpt-4o-mini",
                "--max-exploration",
                "3",
                "--max-sections",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Then: Command should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # And: Metadata should contain cost
        metadata_file = tmp_path / "report.metadata.json"
        assert metadata_file.exists()

        data = json.loads(metadata_file.read_text())
        assert "cost" in data, f"No cost in metadata: {data}"
        assert "total_cost_usd" in data["cost"]
        assert "total_tokens" in data["cost"]
        assert "provider" in data["cost"]
        assert data["cost"]["provider"] == "openrouter"


class TestMetadataSchemaFeature:
    """
    Feature: Metadata Schema
      As a CI/CD pipeline operator
      I want a stable metadata schema
      So that I can parse results programmatically
    """

    def test_metadata_has_version_field(self, tmp_path):
        """
        Scenario: Metadata has version field
          When I generate metadata
          Then it should include a version field
          And the version should be "1.0"
        """
        from tech_writer.metadata import METADATA_VERSION, create_metadata

        output_file = tmp_path / "report.md"
        output_file.write_text("# Report")

        metadata_path = create_metadata(
            output_file=output_file,
            model="test-model",
            repo_path="/test/repo",
            prompt_file="test.txt",
        )

        data = json.loads(metadata_path.read_text())

        assert "version" in data
        assert data["version"] == METADATA_VERSION
        assert data["version"] == "1.0"

    def test_metadata_timestamp_is_utc_iso8601(self, tmp_path):
        """
        Scenario: Timestamp is UTC ISO 8601
          When I generate metadata
          Then the timestamp should be valid ISO 8601
          And it should be in UTC timezone
        """
        from datetime import datetime

        from tech_writer.metadata import create_metadata

        output_file = tmp_path / "report.md"
        output_file.write_text("# Report")

        metadata_path = create_metadata(
            output_file=output_file,
            model="test-model",
            repo_path="/test/repo",
            prompt_file="test.txt",
        )

        data = json.loads(metadata_path.read_text())
        timestamp = data["timestamp"]

        # Should parse as ISO 8601
        parsed = datetime.fromisoformat(timestamp)

        # Should have UTC timezone info
        assert parsed.tzinfo is not None
        assert "+" in timestamp or "Z" in timestamp
