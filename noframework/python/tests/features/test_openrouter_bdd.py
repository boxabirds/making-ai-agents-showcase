"""
BDD-style feature tests for OpenRouter integration.

These tests implement the scenarios from the tech design:
- Generate report with OpenRouter
- Cost tracking is enabled by default
- Disable cost tracking
- Use non-OpenAI model via OpenRouter

Run with: pytest tests/features/test_openrouter_bdd.py -v
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


# Skip all tests if OPENROUTER_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY environment variable not set",
)


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


class TestOpenRouterFeature:
    """
    Feature: OpenRouter Integration
      As a developer
      I want to use OpenRouter as my LLM provider
      So that I can access multiple models and track costs
    """

    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_report_with_openrouter(self, simple_prompt_file, test_repo):
        """
        Scenario: Generate report with OpenRouter
          Given I have an OpenRouter API key
          When I run tech_writer with --provider openrouter
          Then the report should be generated successfully
          And the output should include cost information
        """
        # Given: OPENROUTER_API_KEY is set (checked by pytestmark)

        # When: Run tech_writer with --provider openrouter
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--provider",
                "openrouter",
                "--model",
                "openai/gpt-4o-mini",
                "--max-exploration",
                "5",
                "--max-sections",
                "2",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Then: Report should be generated successfully
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # And: Output should include cost information
        assert "Cost summary:" in result.stderr
        assert "Total cost: $" in result.stderr

    @pytest.mark.integration
    def test_cost_tracking_enabled_by_default(self, simple_prompt_file, test_repo):
        """
        Scenario: Cost tracking is enabled by default
          Given I have an OpenRouter API key
          When I run tech_writer with --provider openrouter
          And I do not specify --no-track-cost
          Then cost tracking should be enabled
          And total_cost_usd should be greater than 0
        """
        # When: Run without --no-track-cost
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
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

        # Then: Cost tracking should be enabled
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Cost summary:" in result.stderr

        # And: total_cost_usd should be greater than 0
        # Extract cost from output
        import re

        cost_match = re.search(r"Total cost: \$(\d+\.\d+)", result.stderr)
        assert cost_match, f"Could not find cost in output: {result.stderr}"
        cost = float(cost_match.group(1))
        assert cost > 0, f"Expected cost > 0, got {cost}"

    @pytest.mark.integration
    def test_disable_cost_tracking(self, simple_prompt_file, test_repo):
        """
        Scenario: Disable cost tracking
          Given I have an OpenRouter API key
          When I run tech_writer with --provider openrouter --no-track-cost
          Then cost tracking should be disabled
          And cost should not appear in the output
        """
        # When: Run with --no-track-cost
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--provider",
                "openrouter",
                "--model",
                "openai/gpt-4o-mini",
                "--no-track-cost",
                "--max-exploration",
                "3",
                "--max-sections",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Then: Cost tracking should be disabled
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # And: Cost should not appear in the output
        assert "Cost summary:" not in result.stderr

    @pytest.mark.integration
    @pytest.mark.slow
    def test_use_non_openai_model_via_openrouter(self, simple_prompt_file, test_repo):
        """
        Scenario: Use non-OpenAI model via OpenRouter
          Given I have an OpenRouter API key
          When I run tech_writer with --provider openrouter --model google/gemini-2.0-flash-001
          Then the report should be generated using Gemini
          And the cost should reflect Gemini pricing
        """
        # When: Run with Google model
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--provider",
                "openrouter",
                "--model",
                "google/gemini-2.0-flash-001",
                "--max-exploration",
                "3",
                "--max-sections",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Then: Report should be generated
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # And: Cost should reflect the model used
        assert "Cost summary:" in result.stderr
        assert "google/gemini-2.0-flash-001" in result.stderr


class TestOpenAIProviderFeature:
    """
    Feature: OpenAI Provider (default)
      As a developer
      I want to use OpenAI directly when I don't need multi-provider access
      So that I can use the default behavior
    """

    @pytest.mark.integration
    def test_openai_provider_no_cost_tracking(self):
        """
        Scenario: OpenAI provider does not track costs
          Given I have an OpenAI API key
          When I use the default provider (openai)
          Then cost tracking should be disabled by default
        """
        from tech_writer.llm import LLMClient

        # Skip if no OpenAI key
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        # When: Use default provider
        client = LLMClient(model="gpt-4o-mini", provider="openai")

        # Then: Cost tracking should be disabled
        assert client.track_cost is False
        assert client.provider == "openai"
