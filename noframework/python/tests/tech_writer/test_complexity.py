"""Unit tests for complexity module."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tech_writer.complexity import (
    BUCKET_LARGE_MAX,
    BUCKET_MEDIUM_MAX,
    BUCKET_SIMPLE_MAX,
    BUDGET_COMPLEX,
    BUDGET_LARGE,
    BUDGET_MEDIUM,
    BUDGET_SIMPLE,
    CARGO_BUILD_TIMEOUT_SECONDS,
    ComplexityBudget,
    _analyze_with_python_fallback,
    _get_cargo_project_path,
    _get_project_root,
    _get_rust_binary_path,
    analyze_complexity,
    ensure_analyzer_built,
    get_analyzer_path,
    get_complexity_context,
    map_complexity_to_budget,
)


class TestComplexityBudget:
    """Tests for ComplexityBudget dataclass."""

    def test_fields(self):
        """ComplexityBudget has expected fields."""
        budget = ComplexityBudget(
            total_cc=5000,
            bucket="medium",
            max_sections=25,
            max_exploration_steps=300,
            section_max_steps=20,
            guidance="Test guidance",
            top_functions=[{"name": "foo", "cc": 10}],
        )

        assert budget.total_cc == 5000
        assert budget.bucket == "medium"
        assert budget.max_sections == 25
        assert budget.max_exploration_steps == 300
        assert budget.section_max_steps == 20
        assert budget.guidance == "Test guidance"
        assert len(budget.top_functions) == 1


class TestMapComplexityToBudget:
    """Tests for map_complexity_to_budget function."""

    def test_simple_bucket_below_threshold(self):
        """Total CC below 5000 maps to simple bucket."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 4999},
            "top_complex_functions": [],
        }
        budget = map_complexity_to_budget(analysis)

        assert budget.bucket == "simple"
        assert budget.max_sections == BUDGET_SIMPLE["max_sections"]
        assert budget.max_exploration_steps == BUDGET_SIMPLE["max_exploration"]

    def test_medium_bucket_at_threshold(self):
        """Total CC at 5000 maps to medium bucket."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 5000},
            "top_complex_functions": [],
        }
        budget = map_complexity_to_budget(analysis)

        assert budget.bucket == "medium"
        assert budget.max_sections == BUDGET_MEDIUM["max_sections"]

    def test_medium_bucket_below_large_threshold(self):
        """Total CC below 25000 maps to medium bucket."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 24999},
            "top_complex_functions": [],
        }
        budget = map_complexity_to_budget(analysis)

        assert budget.bucket == "medium"

    def test_large_bucket_at_threshold(self):
        """Total CC at 25000 maps to large bucket."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 25000},
            "top_complex_functions": [],
        }
        budget = map_complexity_to_budget(analysis)

        assert budget.bucket == "large"
        assert budget.max_sections == BUDGET_LARGE["max_sections"]

    def test_large_bucket_below_complex_threshold(self):
        """Total CC below 100000 maps to large bucket."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 99999},
            "top_complex_functions": [],
        }
        budget = map_complexity_to_budget(analysis)

        assert budget.bucket == "large"

    def test_complex_bucket_at_threshold(self):
        """Total CC at 100000 maps to complex bucket."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 100000},
            "top_complex_functions": [],
        }
        budget = map_complexity_to_budget(analysis)

        assert budget.bucket == "complex"
        assert budget.max_sections == BUDGET_COMPLEX["max_sections"]

    def test_complex_bucket_very_large(self):
        """Very large Total CC maps to complex bucket."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 500000},
            "top_complex_functions": [],
        }
        budget = map_complexity_to_budget(analysis)

        assert budget.bucket == "complex"

    def test_top_functions_extracted(self):
        """Top functions are extracted from analysis."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 1000},
            "top_complex_functions": [
                {"name": "func1", "cyclomatic_complexity": 50},
                {"name": "func2", "cyclomatic_complexity": 40},
            ],
        }
        budget = map_complexity_to_budget(analysis)

        assert len(budget.top_functions) == 2
        assert budget.top_functions[0]["name"] == "func1"

    def test_top_functions_limited_to_ten(self):
        """Top functions are limited to 10."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 1000},
            "top_complex_functions": [{"name": f"func{i}"} for i in range(20)],
        }
        budget = map_complexity_to_budget(analysis)

        assert len(budget.top_functions) == 10

    def test_missing_summary_defaults_to_zero(self):
        """Missing summary defaults to zero (simple bucket)."""
        analysis = {}
        budget = map_complexity_to_budget(analysis)

        assert budget.bucket == "simple"
        assert budget.total_cc == 0

    def test_guidance_included(self):
        """Guidance text is included in budget."""
        analysis = {
            "summary": {"total_cyclomatic_complexity": 1000},
            "top_complex_functions": [],
        }
        budget = map_complexity_to_budget(analysis)

        assert len(budget.guidance) > 0
        assert "codebase" in budget.guidance.lower()


class TestGetAnalyzerPath:
    """Tests for get_analyzer_path function."""

    @patch("shutil.which")
    def test_returns_none_when_not_found(self, mock_which):
        """Returns None when analyzer not in PATH or dev path."""
        mock_which.return_value = None

        # Also need to ensure dev path doesn't exist
        with patch.object(Path, "exists", return_value=False):
            result = get_analyzer_path()

        assert result is None

    @patch("shutil.which")
    def test_finds_in_path(self, mock_which):
        """Returns path when found in PATH."""
        mock_which.return_value = "/usr/local/bin/complexity-analyzer"

        result = get_analyzer_path()

        assert result == Path("/usr/local/bin/complexity-analyzer")

    # Note: test_finds_in_dev_path is covered by integration tests
    # due to complexity of mocking Path resolution


class TestAnalyzeComplexity:
    """Tests for analyze_complexity function.

    Note: These tests now need to mock both Rust and Python fallback
    since analyze_complexity falls back to Python when Rust fails.
    """

    @patch("tech_writer.complexity._analyze_with_python_fallback")
    @patch("tech_writer.complexity.get_analyzer_path")
    def test_returns_none_when_both_fail(self, mock_get_path, mock_python):
        """Returns None when both Rust and Python analyzers fail."""
        mock_get_path.return_value = None
        mock_python.return_value = None

        result = analyze_complexity(Path("/some/repo"))

        assert result is None

    @patch("tech_writer.complexity._analyze_with_python_fallback")
    @patch("tech_writer.complexity.get_analyzer_path")
    @patch("subprocess.run")
    def test_parses_valid_json_output(self, mock_run, mock_get_path, mock_python):
        """Parses valid JSON output from Rust analyzer."""
        mock_get_path.return_value = Path("/usr/bin/complexity-analyzer")

        expected_output = {
            "summary": {"total_cyclomatic_complexity": 1234},
            "top_complex_functions": [],
        }
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(expected_output),
        )

        result = analyze_complexity(Path("/some/repo"))

        assert result == expected_output
        mock_python.assert_not_called()

    @patch("tech_writer.complexity._analyze_with_python_fallback")
    @patch("tech_writer.complexity.get_analyzer_path")
    @patch("subprocess.run")
    def test_falls_back_on_nonzero_exit(self, mock_run, mock_get_path, mock_python):
        """Falls back to Python when Rust analyzer exits with error."""
        mock_get_path.return_value = Path("/usr/bin/complexity-analyzer")
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        expected = {"summary": {"total_cyclomatic_complexity": 5000}}
        mock_python.return_value = expected

        result = analyze_complexity(Path("/some/repo"))

        assert result == expected
        mock_python.assert_called_once()

    @patch("tech_writer.complexity._analyze_with_python_fallback")
    @patch("tech_writer.complexity.get_analyzer_path")
    @patch("subprocess.run")
    def test_falls_back_on_invalid_json(self, mock_run, mock_get_path, mock_python):
        """Falls back to Python when Rust output is not valid JSON."""
        mock_get_path.return_value = Path("/usr/bin/complexity-analyzer")
        mock_run.return_value = MagicMock(returncode=0, stdout="not json")
        expected = {"summary": {"total_cyclomatic_complexity": 6000}}
        mock_python.return_value = expected

        result = analyze_complexity(Path("/some/repo"))

        assert result == expected
        mock_python.assert_called_once()

    @patch("tech_writer.complexity._analyze_with_python_fallback")
    @patch("tech_writer.complexity.get_analyzer_path")
    @patch("subprocess.run")
    def test_falls_back_on_timeout(self, mock_run, mock_get_path, mock_python):
        """Falls back to Python when Rust analyzer times out."""
        mock_get_path.return_value = Path("/usr/bin/complexity-analyzer")
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=300)
        expected = {"summary": {"total_cyclomatic_complexity": 7000}}
        mock_python.return_value = expected

        result = analyze_complexity(Path("/some/repo"))

        assert result == expected
        mock_python.assert_called_once()


class TestGetComplexityContext:
    """Tests for get_complexity_context function."""

    def test_includes_bucket_name(self):
        """Context includes bucket name."""
        budget = ComplexityBudget(
            total_cc=1000,
            bucket="simple",
            max_sections=10,
            max_exploration_steps=100,
            section_max_steps=15,
            guidance="Test guidance",
            top_functions=[],
        )

        context = get_complexity_context(budget)

        assert "**simple**" in context

    def test_includes_total_cc(self):
        """Context includes total cyclomatic complexity."""
        budget = ComplexityBudget(
            total_cc=12345,
            bucket="medium",
            max_sections=25,
            max_exploration_steps=300,
            section_max_steps=20,
            guidance="Test guidance",
            top_functions=[],
        )

        context = get_complexity_context(budget)

        assert "12,345" in context

    def test_includes_guidance(self):
        """Context includes guidance text."""
        budget = ComplexityBudget(
            total_cc=1000,
            bucket="simple",
            max_sections=10,
            max_exploration_steps=100,
            section_max_steps=15,
            guidance="Custom guidance here",
            top_functions=[],
        )

        context = get_complexity_context(budget)

        assert "Custom guidance here" in context

    def test_includes_budget_limits(self):
        """Context includes budget limits."""
        budget = ComplexityBudget(
            total_cc=1000,
            bucket="simple",
            max_sections=10,
            max_exploration_steps=100,
            section_max_steps=15,
            guidance="Test",
            top_functions=[],
        )

        context = get_complexity_context(budget)

        assert "10 sections" in context
        assert "100 exploration steps" in context

    def test_includes_hotspot_functions(self):
        """Context includes top complex functions."""
        budget = ComplexityBudget(
            total_cc=1000,
            bucket="simple",
            max_sections=10,
            max_exploration_steps=100,
            section_max_steps=15,
            guidance="Test",
            top_functions=[
                {
                    "file": "src/core.py",
                    "line": 42,
                    "name": "process_data",
                    "cyclomatic_complexity": 25,
                }
            ],
        )

        context = get_complexity_context(budget)

        assert "src/core.py:42" in context
        assert "process_data" in context
        assert "CC=25" in context

    def test_limits_hotspots_to_five(self):
        """Context shows at most 5 hotspot functions."""
        budget = ComplexityBudget(
            total_cc=1000,
            bucket="simple",
            max_sections=10,
            max_exploration_steps=100,
            section_max_steps=15,
            guidance="Test",
            top_functions=[
                {"file": f"file{i}.py", "line": i, "name": f"func{i}", "cyclomatic_complexity": i}
                for i in range(10)
            ],
        )

        context = get_complexity_context(budget)

        # Should only have 5 functions listed
        assert context.count("func") == 5

    def test_handles_empty_hotspots(self):
        """Context handles empty hotspots list."""
        budget = ComplexityBudget(
            total_cc=1000,
            bucket="simple",
            max_sections=10,
            max_exploration_steps=100,
            section_max_steps=15,
            guidance="Test",
            top_functions=[],
        )

        context = get_complexity_context(budget)

        assert "(none identified)" in context


class TestConstants:
    """Tests for module constants."""

    def test_bucket_thresholds_ordered(self):
        """Bucket thresholds are in ascending order."""
        assert BUCKET_SIMPLE_MAX < BUCKET_MEDIUM_MAX < BUCKET_LARGE_MAX

    def test_budget_sections_scale(self):
        """Budget sections scale with complexity."""
        assert BUDGET_SIMPLE["max_sections"] < BUDGET_MEDIUM["max_sections"]
        assert BUDGET_MEDIUM["max_sections"] < BUDGET_LARGE["max_sections"]
        assert BUDGET_LARGE["max_sections"] < BUDGET_COMPLEX["max_sections"]

    def test_budget_exploration_scales(self):
        """Budget exploration scales with complexity."""
        assert BUDGET_SIMPLE["max_exploration"] < BUDGET_MEDIUM["max_exploration"]
        assert BUDGET_MEDIUM["max_exploration"] < BUDGET_LARGE["max_exploration"]
        assert BUDGET_LARGE["max_exploration"] < BUDGET_COMPLEX["max_exploration"]


class TestHelperFunctions:
    """Tests for path helper functions."""

    def test_get_project_root_returns_path(self):
        """_get_project_root returns a Path."""
        result = _get_project_root()
        assert isinstance(result, Path)

    def test_get_rust_binary_path_returns_path(self):
        """_get_rust_binary_path returns expected path structure."""
        result = _get_rust_binary_path()
        assert isinstance(result, Path)
        assert "complexity-analyzer" in str(result)
        assert "target" in str(result)
        assert "release" in str(result)

    def test_get_cargo_project_path_returns_path(self):
        """_get_cargo_project_path returns expected path structure."""
        result = _get_cargo_project_path()
        assert isinstance(result, Path)
        assert str(result).endswith("complexity-analyzer")


class TestEnsureAnalyzerBuilt:
    """Tests for ensure_analyzer_built function."""

    @patch("tech_writer.complexity._get_rust_binary_path")
    def test_returns_existing_binary(self, mock_get_path):
        """Returns path if binary already exists."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        result = ensure_analyzer_built()

        assert result == mock_path

    @patch("tech_writer.complexity._get_cargo_project_path")
    @patch("tech_writer.complexity._get_rust_binary_path")
    def test_returns_none_when_no_cargo_toml(self, mock_binary_path, mock_cargo_path):
        """Returns None if Cargo.toml doesn't exist."""
        mock_binary = MagicMock(spec=Path)
        mock_binary.exists.return_value = False
        mock_binary_path.return_value = mock_binary

        mock_cargo_dir = MagicMock(spec=Path)
        mock_cargo_toml = MagicMock(spec=Path)
        mock_cargo_toml.exists.return_value = False
        mock_cargo_dir.__truediv__ = MagicMock(return_value=mock_cargo_toml)
        mock_cargo_path.return_value = mock_cargo_dir

        result = ensure_analyzer_built()

        assert result is None

    @patch("shutil.which")
    @patch("tech_writer.complexity._get_cargo_project_path")
    @patch("tech_writer.complexity._get_rust_binary_path")
    def test_returns_none_when_no_cargo_command(self, mock_binary_path, mock_cargo_path, mock_which):
        """Returns None if cargo not in PATH."""
        mock_binary = MagicMock(spec=Path)
        mock_binary.exists.return_value = False
        mock_binary_path.return_value = mock_binary

        mock_cargo_dir = MagicMock(spec=Path)
        mock_cargo_toml = MagicMock(spec=Path)
        mock_cargo_toml.exists.return_value = True
        mock_cargo_dir.__truediv__ = MagicMock(return_value=mock_cargo_toml)
        mock_cargo_path.return_value = mock_cargo_dir

        mock_which.return_value = None

        result = ensure_analyzer_built()

        assert result is None

    @patch("subprocess.run")
    @patch("shutil.which")
    @patch("tech_writer.complexity._get_cargo_project_path")
    @patch("tech_writer.complexity._get_rust_binary_path")
    def test_builds_binary_successfully(self, mock_binary_path, mock_cargo_path, mock_which, mock_run):
        """Builds and returns binary path on success."""
        # Binary doesn't exist initially, then exists after build
        mock_binary = MagicMock(spec=Path)
        mock_binary.exists.side_effect = [False, True]  # First check: no, after build: yes
        mock_binary_path.return_value = mock_binary

        mock_cargo_dir = MagicMock(spec=Path)
        mock_cargo_toml = MagicMock(spec=Path)
        mock_cargo_toml.exists.return_value = True
        mock_cargo_dir.__truediv__ = MagicMock(return_value=mock_cargo_toml)
        mock_cargo_path.return_value = mock_cargo_dir

        mock_which.return_value = "/usr/bin/cargo"
        mock_run.return_value = MagicMock(returncode=0)

        result = ensure_analyzer_built()

        assert result == mock_binary
        mock_run.assert_called_once()

    @patch("subprocess.run")
    @patch("shutil.which")
    @patch("tech_writer.complexity._get_cargo_project_path")
    @patch("tech_writer.complexity._get_rust_binary_path")
    def test_returns_none_on_build_failure(self, mock_binary_path, mock_cargo_path, mock_which, mock_run):
        """Returns None when cargo build fails."""
        mock_binary = MagicMock(spec=Path)
        mock_binary.exists.return_value = False
        mock_binary_path.return_value = mock_binary

        mock_cargo_dir = MagicMock(spec=Path)
        mock_cargo_toml = MagicMock(spec=Path)
        mock_cargo_toml.exists.return_value = True
        mock_cargo_dir.__truediv__ = MagicMock(return_value=mock_cargo_toml)
        mock_cargo_path.return_value = mock_cargo_dir

        mock_which.return_value = "/usr/bin/cargo"
        mock_run.return_value = MagicMock(returncode=1, stderr="build error")

        result = ensure_analyzer_built()

        assert result is None

    @patch("subprocess.run")
    @patch("shutil.which")
    @patch("tech_writer.complexity._get_cargo_project_path")
    @patch("tech_writer.complexity._get_rust_binary_path")
    def test_returns_none_on_build_timeout(self, mock_binary_path, mock_cargo_path, mock_which, mock_run):
        """Returns None when cargo build times out."""
        mock_binary = MagicMock(spec=Path)
        mock_binary.exists.return_value = False
        mock_binary_path.return_value = mock_binary

        mock_cargo_dir = MagicMock(spec=Path)
        mock_cargo_toml = MagicMock(spec=Path)
        mock_cargo_toml.exists.return_value = True
        mock_cargo_dir.__truediv__ = MagicMock(return_value=mock_cargo_toml)
        mock_cargo_path.return_value = mock_cargo_dir

        mock_which.return_value = "/usr/bin/cargo"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="cargo", timeout=CARGO_BUILD_TIMEOUT_SECONDS)

        result = ensure_analyzer_built()

        assert result is None


class TestPythonFallback:
    """Tests for _analyze_with_python_fallback function."""

    @patch("tech_writer.complexity._get_project_root")
    def test_returns_none_when_poc_not_found(self, mock_root):
        """Returns None if POC directory doesn't exist."""
        mock_root.return_value = Path("/nonexistent/path")

        result = _analyze_with_python_fallback(Path("/some/repo"))

        assert result is None

    @patch("tech_writer.complexity._get_project_root")
    def test_returns_dict_format(self, mock_root, tmp_path):
        """Returns dict in expected format when successful."""
        # Create a mock POC directory structure
        poc_dir = tmp_path / "pocs" / "code-base-complexity"
        poc_dir.mkdir(parents=True)

        # Write a minimal mock complexity_analyzer module
        mock_analyzer = poc_dir / "complexity_analyzer.py"
        mock_analyzer.write_text('''
from dataclasses import dataclass

@dataclass
class RepoMetrics:
    repository: str
    scan_time_ms: int
    summary: dict
    distribution: dict
    top_complex_functions: list

def analyze_repository(repo_path, repo_name, parallel=False):
    return RepoMetrics(
        repository=repo_name,
        scan_time_ms=100,
        summary={"total_cyclomatic_complexity": 1000},
        distribution={"low": 10, "medium": 5, "high": 2},
        top_complex_functions=[],
    )
''')

        mock_root.return_value = tmp_path

        result = _analyze_with_python_fallback(Path("/some/repo"))

        assert result is not None
        assert "summary" in result
        assert "top_complex_functions" in result


class TestFallbackChain:
    """Tests for the full fallback chain in analyze_complexity."""

    @patch("tech_writer.complexity._analyze_with_python_fallback")
    @patch("tech_writer.complexity._analyze_with_rust")
    @patch("tech_writer.complexity.get_analyzer_path")
    def test_uses_rust_when_available(self, mock_get_path, mock_rust, mock_python):
        """Uses Rust analyzer when available."""
        mock_get_path.return_value = Path("/usr/bin/complexity-analyzer")
        expected = {"summary": {"total_cyclomatic_complexity": 1000}}
        mock_rust.return_value = expected

        result = analyze_complexity(Path("/repo"))

        assert result == expected
        mock_rust.assert_called_once()
        mock_python.assert_not_called()

    @patch("tech_writer.complexity._analyze_with_python_fallback")
    @patch("tech_writer.complexity._analyze_with_rust")
    @patch("tech_writer.complexity.get_analyzer_path")
    def test_falls_back_to_python_when_rust_fails(self, mock_get_path, mock_rust, mock_python):
        """Falls back to Python when Rust fails."""
        mock_get_path.return_value = Path("/usr/bin/complexity-analyzer")
        mock_rust.return_value = None
        expected = {"summary": {"total_cyclomatic_complexity": 2000}}
        mock_python.return_value = expected

        result = analyze_complexity(Path("/repo"))

        assert result == expected
        mock_rust.assert_called_once()
        mock_python.assert_called_once()

    @patch("tech_writer.complexity._analyze_with_python_fallback")
    @patch("tech_writer.complexity.get_analyzer_path")
    def test_uses_python_directly_when_no_rust(self, mock_get_path, mock_python):
        """Uses Python directly when Rust not available."""
        mock_get_path.return_value = None
        expected = {"summary": {"total_cyclomatic_complexity": 3000}}
        mock_python.return_value = expected

        result = analyze_complexity(Path("/repo"))

        assert result == expected
        mock_python.assert_called_once()

    @patch("tech_writer.complexity._analyze_with_python_fallback")
    @patch("tech_writer.complexity.get_analyzer_path")
    def test_returns_none_when_all_fail(self, mock_get_path, mock_python):
        """Returns None when both Rust and Python fail."""
        mock_get_path.return_value = None
        mock_python.return_value = None

        result = analyze_complexity(Path("/repo"))

        assert result is None
