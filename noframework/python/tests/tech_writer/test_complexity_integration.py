"""Integration tests for complexity module.

These tests require the complexity analyzer to be available.
They test real analyzer execution against actual code.
"""

import json
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
    get_analyzer_path,
    map_complexity_to_budget,
    _get_project_root,
)


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


def analyzer_available() -> bool:
    """Check if any analyzer (Rust or Python fallback) is available."""
    return get_analyzer_path() is not None or (_get_project_root() / "pocs" / "code-base-complexity").exists()


@pytest.fixture
def test_repo_path() -> Path:
    """Return path to a test repository (this repo itself)."""
    return _get_project_root()


class TestRealAnalyzerExecution:
    """Tests for real analyzer execution."""

    @pytest.mark.skipif(not analyzer_available(), reason="No analyzer available")
    def test_analyzes_this_repository(self, test_repo_path: Path):
        """Analyze this repository and verify JSON structure."""
        result = analyze_complexity(test_repo_path)

        # Should return a result (using either Rust or Python fallback)
        assert result is not None

        # Verify JSON structure
        assert "summary" in result
        assert "total_cyclomatic_complexity" in result["summary"]
        assert "top_complex_functions" in result
        assert isinstance(result["top_complex_functions"], list)

    @pytest.mark.skipif(not analyzer_available(), reason="No analyzer available")
    def test_summary_contains_required_fields(self, test_repo_path: Path):
        """Summary contains all required fields."""
        result = analyze_complexity(test_repo_path)
        assert result is not None

        summary = result["summary"]
        required_fields = [
            "total_files",
            "total_functions",
            "total_cyclomatic_complexity",
            "complexity_bucket",
        ]
        for field in required_fields:
            assert field in summary, f"Missing field: {field}"

    @pytest.mark.skipif(not analyzer_available(), reason="No analyzer available")
    def test_total_cc_is_positive(self, test_repo_path: Path):
        """Total cyclomatic complexity is positive for this repo."""
        result = analyze_complexity(test_repo_path)
        assert result is not None

        total_cc = result["summary"]["total_cyclomatic_complexity"]
        # This repo should have at least some complexity
        assert total_cc > 0

    @pytest.mark.skipif(not analyzer_available(), reason="No analyzer available")
    def test_bucket_assignment_reasonable(self, test_repo_path: Path):
        """Bucket assignment is reasonable for this repo."""
        result = analyze_complexity(test_repo_path)
        assert result is not None

        bucket = result["summary"]["complexity_bucket"]
        # This repo is small/medium, not complex
        assert bucket in ["simple", "medium", "large"]


class TestBucketAssignment:
    """Tests for complexity bucket assignment."""

    def test_simple_bucket_boundary(self):
        """Total CC below 5000 maps to simple bucket."""
        analysis = {"summary": {"total_cyclomatic_complexity": BUCKET_SIMPLE_MAX - 1}}
        budget = map_complexity_to_budget(analysis)
        assert budget.bucket == "simple"
        assert budget.max_sections == BUDGET_SIMPLE["max_sections"]

    def test_medium_bucket_boundary(self):
        """Total CC at 5000 maps to medium bucket."""
        analysis = {"summary": {"total_cyclomatic_complexity": BUCKET_SIMPLE_MAX}}
        budget = map_complexity_to_budget(analysis)
        assert budget.bucket == "medium"
        assert budget.max_sections == BUDGET_MEDIUM["max_sections"]

    def test_large_bucket_boundary(self):
        """Total CC at 25000 maps to large bucket."""
        analysis = {"summary": {"total_cyclomatic_complexity": BUCKET_MEDIUM_MAX}}
        budget = map_complexity_to_budget(analysis)
        assert budget.bucket == "large"
        assert budget.max_sections == BUDGET_LARGE["max_sections"]

    def test_complex_bucket_boundary(self):
        """Total CC at 100000 maps to complex bucket."""
        analysis = {"summary": {"total_cyclomatic_complexity": BUCKET_LARGE_MAX}}
        budget = map_complexity_to_budget(analysis)
        assert budget.bucket == "complex"
        assert budget.max_sections == BUDGET_COMPLEX["max_sections"]


class TestBudgetLimitsApplied:
    """Tests for budget limits being correctly applied."""

    def test_simple_budget_limits(self):
        """Simple repos get constrained limits."""
        analysis = {"summary": {"total_cyclomatic_complexity": 1000}}
        budget = map_complexity_to_budget(analysis)

        assert budget.max_sections == 10
        assert budget.max_exploration_steps == 100
        assert budget.section_max_steps == 15

    def test_medium_budget_limits(self):
        """Medium repos get moderate limits."""
        analysis = {"summary": {"total_cyclomatic_complexity": 15000}}
        budget = map_complexity_to_budget(analysis)

        assert budget.max_sections == 25
        assert budget.max_exploration_steps == 300
        assert budget.section_max_steps == 20

    def test_large_budget_limits(self):
        """Large repos get expanded limits."""
        analysis = {"summary": {"total_cyclomatic_complexity": 75000}}
        budget = map_complexity_to_budget(analysis)

        assert budget.max_sections == 40
        assert budget.max_exploration_steps == 500
        assert budget.section_max_steps == 25

    def test_complex_budget_limits(self):
        """Complex repos get maximum limits."""
        analysis = {"summary": {"total_cyclomatic_complexity": 200000}}
        budget = map_complexity_to_budget(analysis)

        assert budget.max_sections == 50
        assert budget.max_exploration_steps == 800
        assert budget.section_max_steps == 30


class TestFallbackBehavior:
    """Tests for fallback behavior when analyzer unavailable."""

    @patch("tech_writer.complexity.get_analyzer_path")
    @patch("tech_writer.complexity._analyze_with_python_fallback")
    def test_returns_none_when_all_analyzers_fail(self, mock_python, mock_get_path):
        """Returns None when both Rust and Python analyzers are unavailable."""
        mock_get_path.return_value = None
        mock_python.return_value = None

        result = analyze_complexity(Path("/some/repo"))

        assert result is None

    def test_budget_defaults_reasonable(self):
        """Default budget values are reasonable."""
        # If analyze_complexity returns None, caller should use defaults
        # Verify default values match medium bucket (reasonable defaults)
        from tech_writer.orchestrator import DEFAULT_MAX_SECTIONS, DEFAULT_MAX_STEPS

        # Defaults should be in reasonable range
        assert DEFAULT_MAX_SECTIONS >= BUDGET_SIMPLE["max_sections"]
        assert DEFAULT_MAX_SECTIONS <= BUDGET_COMPLEX["max_sections"]
        assert DEFAULT_MAX_STEPS >= BUDGET_SIMPLE["max_exploration"]
        assert DEFAULT_MAX_STEPS <= BUDGET_COMPLEX["max_exploration"]


class TestTopComplexFunctions:
    """Tests for top complex functions extraction."""

    @pytest.mark.skipif(not analyzer_available(), reason="No analyzer available")
    def test_top_functions_have_required_fields(self, test_repo_path: Path):
        """Top complex functions have required fields."""
        result = analyze_complexity(test_repo_path)
        assert result is not None

        top_funcs = result["top_complex_functions"]
        if len(top_funcs) > 0:
            func = top_funcs[0]
            # Should have these fields
            assert "file" in func
            assert "name" in func
            assert "cyclomatic_complexity" in func

    @pytest.mark.skipif(not analyzer_available(), reason="No analyzer available")
    def test_top_functions_sorted_by_complexity(self, test_repo_path: Path):
        """Top complex functions are sorted by complexity (highest first)."""
        result = analyze_complexity(test_repo_path)
        assert result is not None

        top_funcs = result["top_complex_functions"]
        if len(top_funcs) > 1:
            complexities = [f["cyclomatic_complexity"] for f in top_funcs]
            # Should be in descending order
            assert complexities == sorted(complexities, reverse=True)
