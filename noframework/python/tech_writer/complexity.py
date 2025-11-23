"""
Complexity analysis integration for proportional documentation budgets.

Runs the Rust complexity analyzer to measure Total Cyclomatic Complexity,
then maps to documentation budget (sections, exploration steps).

Fallback chain:
1. Rust binary in PATH
2. Rust binary in tools/complexity-analyzer/
3. Build Rust binary (if cargo available)
4. Python fallback
5. Return None (use defaults)
"""

import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Bucket thresholds (must match Rust implementation)
BUCKET_SIMPLE_MAX = 5_000
BUCKET_MEDIUM_MAX = 25_000
BUCKET_LARGE_MAX = 100_000

# Budget constants per bucket
BUDGET_SIMPLE = {"max_sections": 10, "max_exploration": 100, "section_max_steps": 15}
BUDGET_MEDIUM = {"max_sections": 25, "max_exploration": 300, "section_max_steps": 20}
BUDGET_LARGE = {"max_sections": 40, "max_exploration": 500, "section_max_steps": 25}
BUDGET_COMPLEX = {"max_sections": 50, "max_exploration": 800, "section_max_steps": 30}

# Analyzer timeout in seconds
ANALYZER_TIMEOUT_SECONDS = 300

# Cargo build timeout in seconds
CARGO_BUILD_TIMEOUT_SECONDS = 120


def _get_project_root() -> Path:
    """Get the project root directory (parent of tech_writer module)."""
    return Path(__file__).parent.parent


def _get_rust_binary_path() -> Path:
    """Get the expected path for the Rust binary in development."""
    return _get_project_root() / "tools" / "complexity-analyzer" / "target" / "release" / "complexity-analyzer"


def _get_cargo_project_path() -> Path:
    """Get the path to the Rust complexity-analyzer project."""
    return _get_project_root() / "tools" / "complexity-analyzer"


def ensure_analyzer_built() -> Optional[Path]:
    """
    Build the Rust complexity analyzer if cargo is available and binary is missing.

    Returns:
        Path to binary if build succeeds or already exists, None otherwise
    """
    binary_path = _get_rust_binary_path()

    # Already built
    if binary_path.exists():
        return binary_path

    # Check if Cargo.toml exists (we're in the right repo)
    cargo_project = _get_cargo_project_path()
    cargo_toml = cargo_project / "Cargo.toml"
    if not cargo_toml.exists():
        logger.debug("Cargo.toml not found at %s, skipping build", cargo_toml)
        return None

    # Check if cargo is available
    if shutil.which("cargo") is None:
        logger.debug("cargo not found in PATH, cannot build analyzer")
        return None

    # Attempt build
    logger.info("Building complexity-analyzer with cargo...")
    try:
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=str(cargo_project),
            capture_output=True,
            text=True,
            timeout=CARGO_BUILD_TIMEOUT_SECONDS,
        )
        if result.returncode == 0:
            logger.info("Successfully built complexity-analyzer")
            return binary_path if binary_path.exists() else None
        else:
            logger.warning("cargo build failed: %s", result.stderr[:500] if result.stderr else "unknown error")
            return None
    except subprocess.TimeoutExpired:
        logger.warning("cargo build timed out after %d seconds", CARGO_BUILD_TIMEOUT_SECONDS)
        return None
    except FileNotFoundError:
        logger.debug("cargo command failed to execute")
        return None


@dataclass
class ComplexityBudget:
    """Documentation budget derived from complexity analysis."""

    total_cc: int
    bucket: str
    max_sections: int
    max_exploration_steps: int
    section_max_steps: int
    guidance: str
    top_functions: list[dict]


def get_analyzer_path() -> Optional[Path]:
    """
    Find the complexity analyzer binary.

    Search order:
    1. In PATH (for installed binary)
    2. Pre-built binary in development location
    3. Build on demand (if cargo available)

    Returns:
        Path to binary if found, None otherwise
    """
    # 1. Check if in PATH
    which_result = shutil.which("complexity-analyzer")
    if which_result:
        return Path(which_result)

    # 2. Check pre-built binary in development location
    dev_path = _get_rust_binary_path()
    if dev_path.exists():
        return dev_path

    # 3. Try to build on demand
    built_path = ensure_analyzer_built()
    if built_path:
        return built_path

    return None


def _analyze_with_rust(repo_path: Path, analyzer: Path) -> Optional[dict]:
    """
    Run Rust complexity analyzer.

    Args:
        repo_path: Path to the repository to analyze
        analyzer: Path to the Rust binary

    Returns:
        Parsed JSON output from analyzer, or None on error
    """
    try:
        result = subprocess.run(
            [str(analyzer), "--path", str(repo_path)],
            capture_output=True,
            text=True,
            timeout=ANALYZER_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            logger.debug("Rust analyzer returned non-zero: %s", result.stderr[:200] if result.stderr else "")
            return None

        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        logger.warning("Rust analyzer timed out after %d seconds", ANALYZER_TIMEOUT_SECONDS)
        return None
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse Rust analyzer output: %s", e)
        return None
    except FileNotFoundError:
        logger.debug("Rust analyzer binary not found at runtime")
        return None


def _analyze_with_python_fallback(repo_path: Path) -> Optional[dict]:
    """
    Analyze repository using Python fallback implementation.

    This is slower than Rust but provides functionality when Rust is unavailable.

    Args:
        repo_path: Path to the repository to analyze

    Returns:
        Parsed JSON output compatible with Rust format, or None on error
    """
    try:
        # Add POC directory to path temporarily
        poc_dir = _get_project_root() / "pocs" / "code-base-complexity"
        if not poc_dir.exists():
            logger.debug("Python fallback POC not found at %s", poc_dir)
            return None

        # Import the POC module
        if str(poc_dir) not in sys.path:
            sys.path.insert(0, str(poc_dir))

        try:
            from complexity_analyzer import analyze_repository
        except ImportError as e:
            logger.warning("Failed to import Python fallback analyzer: %s", e)
            return None
        finally:
            # Clean up sys.path
            if str(poc_dir) in sys.path:
                sys.path.remove(str(poc_dir))

        logger.warning(
            "Using Python fallback analyzer (slower than Rust). "
            "Build Rust analyzer for better performance: cd tools/complexity-analyzer && cargo build --release"
        )

        # Run analysis
        repo_name = repo_path.name
        metrics = analyze_repository(repo_path, repo_name, parallel=False)

        # Convert to JSON-compatible dict (same format as Rust)
        return {
            "repository": metrics.repository,
            "scan_time_ms": metrics.scan_time_ms,
            "summary": metrics.summary,
            "distribution": metrics.distribution,
            "top_complex_functions": metrics.top_complex_functions,
        }
    except Exception as e:
        logger.warning("Python fallback analysis failed: %s", e)
        return None


def analyze_complexity(repo_path: Path) -> Optional[dict]:
    """
    Run complexity analyzer on a repository.

    Tries Rust analyzer first, then falls back to Python implementation.

    Fallback chain:
    1. Rust binary (PATH or development location or build-on-demand)
    2. Python fallback (pocs/code-base-complexity)
    3. Return None (caller should use defaults)

    Args:
        repo_path: Path to the repository to analyze

    Returns:
        Parsed JSON output from analyzer, or None on error
    """
    # Try Rust analyzer first
    analyzer = get_analyzer_path()
    if analyzer:
        result = _analyze_with_rust(repo_path, analyzer)
        if result:
            return result
        logger.debug("Rust analyzer failed, trying Python fallback")

    # Fall back to Python
    return _analyze_with_python_fallback(repo_path)


def map_complexity_to_budget(analysis: dict) -> ComplexityBudget:
    """
    Map complexity analysis to documentation budget.

    Args:
        analysis: Parsed JSON output from complexity analyzer

    Returns:
        ComplexityBudget with appropriate limits for the codebase size
    """
    summary = analysis.get("summary", {})
    total_cc = summary.get("total_cyclomatic_complexity", 0)
    top_functions = analysis.get("top_complex_functions", [])[:10]

    if total_cc < BUCKET_SIMPLE_MAX:
        return ComplexityBudget(
            total_cc=total_cc,
            bucket="simple",
            max_sections=BUDGET_SIMPLE["max_sections"],
            max_exploration_steps=BUDGET_SIMPLE["max_exploration"],
            section_max_steps=BUDGET_SIMPLE["section_max_steps"],
            guidance="Small, focused codebase. Cover all major components thoroughly.",
            top_functions=top_functions,
        )
    elif total_cc < BUCKET_MEDIUM_MAX:
        return ComplexityBudget(
            total_cc=total_cc,
            bucket="medium",
            max_sections=BUDGET_MEDIUM["max_sections"],
            max_exploration_steps=BUDGET_MEDIUM["max_exploration"],
            section_max_steps=BUDGET_MEDIUM["section_max_steps"],
            guidance="Medium codebase. Focus on architecture and key modules. Summarize peripheral code.",
            top_functions=top_functions,
        )
    elif total_cc < BUCKET_LARGE_MAX:
        return ComplexityBudget(
            total_cc=total_cc,
            bucket="large",
            max_sections=BUDGET_LARGE["max_sections"],
            max_exploration_steps=BUDGET_LARGE["max_exploration"],
            section_max_steps=BUDGET_LARGE["section_max_steps"],
            guidance="Large codebase. Prioritize core systems and complex hotspots. Use high-level summaries for stable/simple areas.",
            top_functions=top_functions,
        )
    else:
        return ComplexityBudget(
            total_cc=total_cc,
            bucket="complex",
            max_sections=BUDGET_COMPLEX["max_sections"],
            max_exploration_steps=BUDGET_COMPLEX["max_exploration"],
            section_max_steps=BUDGET_COMPLEX["section_max_steps"],
            guidance="Massive codebase. Focus on architecture, entry points, and the top complex functions. Cannot cover everything - prioritize what helps newcomers navigate.",
            top_functions=top_functions,
        )


def get_complexity_context(budget: ComplexityBudget) -> str:
    """
    Generate context string for LLM prompts.

    Args:
        budget: ComplexityBudget from analysis

    Returns:
        Formatted string to inject into LLM system prompts
    """
    hotspots_lines = []
    for func in budget.top_functions[:5]:
        file_path = func.get("file", "unknown")
        line = func.get("line", 0)
        name = func.get("name", "unknown")
        cc = func.get("cyclomatic_complexity", 0)
        hotspots_lines.append(f"  - {file_path}:{line} {name} (CC={cc})")

    hotspots = "\n".join(hotspots_lines) if hotspots_lines else "  (none identified)"

    return f"""## Codebase Complexity Analysis

This is a **{budget.bucket}** codebase ({budget.total_cc:,} total cyclomatic complexity).

**Documentation Strategy**: {budget.guidance}

**Complex Hotspots to Cover**:
{hotspots}

**Budget**: Up to {budget.max_sections} sections, {budget.max_exploration_steps} exploration steps.
"""
