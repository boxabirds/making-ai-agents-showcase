"""
BDD-style feature tests for proportional complexity.

These tests implement the scenarios from the tech design:
- Automatic budget scaling based on codebase complexity
- Skip complexity analysis with --skip-complexity
- Dry run mode with --dry-run
- Graceful degradation when analyzer unavailable

Run with: pytest tests/features/test_complexity_bdd.py -v
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tech_writer.complexity import (
    BUCKET_SIMPLE_MAX,
    BUCKET_MEDIUM_MAX,
    BUCKET_LARGE_MAX,
    BUDGET_SIMPLE,
    BUDGET_MEDIUM,
    BUDGET_LARGE,
    BUDGET_COMPLEX,
    analyze_complexity,
    map_complexity_to_budget,
    get_analyzer_path,
    _get_project_root,
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


def analyzer_available() -> bool:
    """Check if any analyzer (Rust or Python fallback) is available."""
    return get_analyzer_path() is not None or (_get_project_root() / "pocs" / "code-base-complexity").exists()


class TestAutomaticBudgetScalingFeature:
    """
    Feature: Automatic Budget Scaling
      As a tech writer user
      I want documentation effort to scale with codebase complexity
      So that simple repos get quick docs and complex repos get thorough coverage
    """

    def test_simple_codebase_gets_constrained_budget(self):
        """
        Scenario: Simple codebase gets constrained budget
          Given a simple codebase (Total CC < 5000)
          When I analyze the complexity
          Then max_sections should be 10
          And max_exploration should be 100
        """
        # Given: A simple codebase
        analysis = {
            "summary": {"total_cyclomatic_complexity": 3000},
            "top_complex_functions": [],
        }

        # When: I analyze the complexity
        budget = map_complexity_to_budget(analysis)

        # Then: max_sections should be 10
        assert budget.max_sections == 10

        # And: max_exploration should be 100
        assert budget.max_exploration_steps == 100
        assert budget.bucket == "simple"

    def test_medium_codebase_gets_moderate_budget(self):
        """
        Scenario: Medium codebase gets moderate budget
          Given a medium codebase (5000 <= Total CC < 25000)
          When I analyze the complexity
          Then max_sections should be 25
          And max_exploration should be 300
        """
        # Given: A medium codebase
        analysis = {
            "summary": {"total_cyclomatic_complexity": 15000},
            "top_complex_functions": [],
        }

        # When: I analyze the complexity
        budget = map_complexity_to_budget(analysis)

        # Then: max_sections should be 25
        assert budget.max_sections == 25

        # And: max_exploration should be 300
        assert budget.max_exploration_steps == 300
        assert budget.bucket == "medium"

    def test_large_codebase_gets_expanded_budget(self):
        """
        Scenario: Large codebase gets expanded budget
          Given a large codebase (25000 <= Total CC < 100000)
          When I analyze the complexity
          Then max_sections should be 40
          And max_exploration should be 500
        """
        # Given: A large codebase
        analysis = {
            "summary": {"total_cyclomatic_complexity": 75000},
            "top_complex_functions": [],
        }

        # When: I analyze the complexity
        budget = map_complexity_to_budget(analysis)

        # Then: max_sections should be 40
        assert budget.max_sections == 40

        # And: max_exploration should be 500
        assert budget.max_exploration_steps == 500
        assert budget.bucket == "large"

    def test_complex_codebase_gets_maximum_budget(self):
        """
        Scenario: Complex codebase gets maximum budget
          Given a complex codebase (Total CC >= 100000)
          When I analyze the complexity
          Then max_sections should be 50
          And max_exploration should be 800
        """
        # Given: A complex codebase
        analysis = {
            "summary": {"total_cyclomatic_complexity": 200000},
            "top_complex_functions": [],
        }

        # When: I analyze the complexity
        budget = map_complexity_to_budget(analysis)

        # Then: max_sections should be 50
        assert budget.max_sections == 50

        # And: max_exploration should be 800
        assert budget.max_exploration_steps == 800
        assert budget.bucket == "complex"


class TestSkipComplexityFeature:
    """
    Feature: Skip Complexity Analysis
      As a user who knows their codebase
      I want to skip complexity analysis
      So that I can use default budgets or my own settings
    """

    def test_skip_complexity_flag_accepted(self, simple_prompt_file, test_repo):
        """
        Scenario: Skip complexity flag is accepted
          When I run tech_writer with --skip-complexity --dry-run
          Then the command should succeed
          And complexity analysis should be skipped
        """
        # When: Run with --skip-complexity --dry-run
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--skip-complexity",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Then: Command should succeed (dry-run exits 0)
        assert result.returncode == 0

        # And: Should not show complexity analysis
        assert "Analyzing codebase complexity" not in result.stderr

    def test_skip_complexity_uses_default_budgets(self, simple_prompt_file, test_repo):
        """
        Scenario: Skip complexity uses default budgets
          When I run tech_writer with --skip-complexity --dry-run
          Then default budgets should be implied (no complexity info shown)
        """
        # When: Run with --skip-complexity --dry-run
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--skip-complexity",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Then: Should not show bucket info
        assert "Total CC" not in result.stderr
        assert result.returncode == 0


class TestDryRunFeature:
    """
    Feature: Dry Run Mode
      As a user planning a documentation run
      I want to preview complexity analysis
      So that I can understand budgets before running the full pipeline
    """

    @pytest.mark.skipif(not analyzer_available(), reason="No analyzer available")
    def test_dry_run_shows_complexity_metrics(self, simple_prompt_file, test_repo):
        """
        Scenario: Dry run shows complexity metrics
          When I run tech_writer with --dry-run
          Then complexity metrics should be displayed
          And pipeline should not run
        """
        # When: Run with --dry-run
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tech_writer",
                "--prompt",
                str(simple_prompt_file),
                "--repo",
                str(test_repo),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Then: Command should succeed
        assert result.returncode == 0

        # And: Should show complexity analysis
        assert "Complexity:" in result.stderr or "Analyzing codebase complexity" in result.stderr

        # And: Should show dry run message
        assert "Dry run complete" in result.stderr

    def test_dry_run_does_not_require_api_key(self, simple_prompt_file, test_repo):
        """
        Scenario: Dry run does not require API key
          When I run tech_writer with --dry-run
          Then no API calls should be made
          And command should succeed without API key
        """
        import os

        # Save existing keys
        saved_keys = {
            "OPENAI_API_KEY": os.environ.pop("OPENAI_API_KEY", None),
            "OPENROUTER_API_KEY": os.environ.pop("OPENROUTER_API_KEY", None),
        }

        try:
            # When: Run with --dry-run and no API keys
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tech_writer",
                    "--prompt",
                    str(simple_prompt_file),
                    "--repo",
                    str(test_repo),
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                env={k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "OPENROUTER_API_KEY")},
            )

            # Then: Should succeed (no API calls needed)
            assert result.returncode == 0
            assert "Dry run complete" in result.stderr
        finally:
            # Restore keys
            for key, value in saved_keys.items():
                if value is not None:
                    os.environ[key] = value


class TestGracefulDegradationFeature:
    """
    Feature: Graceful Degradation
      As a user without the Rust analyzer
      I want tech_writer to still work
      So that I can generate documentation using default budgets or Python fallback
    """

    @patch("tech_writer.complexity.get_analyzer_path")
    @patch("tech_writer.complexity._analyze_with_python_fallback")
    def test_uses_defaults_when_analyzer_unavailable(self, mock_python, mock_get_path):
        """
        Scenario: Uses defaults when analyzer unavailable
          Given the complexity analyzer is unavailable
          When I analyze complexity
          Then None should be returned
          And the caller should use default budgets
        """
        # Given: Analyzer unavailable
        mock_get_path.return_value = None
        mock_python.return_value = None

        # When: I analyze complexity
        result = analyze_complexity(Path("/some/repo"))

        # Then: None should be returned
        assert result is None

    def test_default_budgets_are_reasonable(self):
        """
        Scenario: Default budgets are reasonable
          Given complexity analysis fails
          When default budgets are used
          Then they should be in the medium range
        """
        from tech_writer.orchestrator import DEFAULT_MAX_SECTIONS, DEFAULT_MAX_STEPS

        # Default should be reasonable (medium-ish)
        assert DEFAULT_MAX_SECTIONS >= BUDGET_SIMPLE["max_sections"]
        assert DEFAULT_MAX_SECTIONS <= BUDGET_COMPLEX["max_sections"]

    @pytest.mark.skipif(not analyzer_available(), reason="No analyzer available")
    def test_analysis_works_with_available_analyzer(self, test_repo):
        """
        Scenario: Analysis works when analyzer available
          Given the analyzer is available
          When I analyze a repository
          Then I should get valid results
        """
        # Given: Analyzer is available (skipif handles this)
        # When: I analyze the repo
        result = analyze_complexity(test_repo)

        # Then: Should get valid results
        assert result is not None
        assert "summary" in result
        assert "total_cyclomatic_complexity" in result["summary"]


class TestBudgetBoundariesFeature:
    """
    Feature: Budget Boundaries
      As a tech writer user
      I want clear bucket boundaries
      So that I understand how budgets scale
    """

    @pytest.mark.parametrize(
        "total_cc,expected_bucket",
        [
            (0, "simple"),
            (4999, "simple"),
            (5000, "medium"),
            (24999, "medium"),
            (25000, "large"),
            (99999, "large"),
            (100000, "complex"),
            (500000, "complex"),
        ],
    )
    def test_bucket_boundary_assignment(self, total_cc, expected_bucket):
        """
        Scenario Outline: Bucket boundaries
          Given Total CC is <total_cc>
          When I map to budget
          Then bucket should be <expected_bucket>
        """
        analysis = {"summary": {"total_cyclomatic_complexity": total_cc}}
        budget = map_complexity_to_budget(analysis)
        assert budget.bucket == expected_bucket

    @pytest.mark.parametrize(
        "bucket,expected_sections,expected_exploration",
        [
            ("simple", 10, 100),
            ("medium", 25, 300),
            ("large", 40, 500),
            ("complex", 50, 800),
        ],
    )
    def test_budget_values_for_buckets(self, bucket, expected_sections, expected_exploration):
        """
        Scenario Outline: Budget values for buckets
          Given a <bucket> bucket
          Then max_sections should be <expected_sections>
          And max_exploration should be <expected_exploration>
        """
        # Map bucket to a representative CC value
        cc_values = {
            "simple": 1000,
            "medium": 15000,
            "large": 75000,
            "complex": 200000,
        }
        analysis = {"summary": {"total_cyclomatic_complexity": cc_values[bucket]}}
        budget = map_complexity_to_budget(analysis)

        assert budget.max_sections == expected_sections
        assert budget.max_exploration_steps == expected_exploration
