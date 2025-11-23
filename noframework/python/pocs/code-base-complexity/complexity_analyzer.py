#!/usr/bin/env python3
"""
Codebase Complexity Analyzer

Analyzes code complexity using tree-sitter AST parsing with .gitignore support.
Produces language-agnostic metrics for scaling documentation effort.

Usage:
    python complexity_analyzer.py --path /path/to/repo
    python complexity_analyzer.py --repo https://github.com/axios/axios
"""

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import pathspec
from tree_sitter_languages import get_parser

from normalized_nodes import (
    get_language,
    is_function_node,
    is_decision_point,
    is_nesting_node,
    get_boolean_operators,
    get_supported_languages,
)


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""
    file: str
    name: str
    line: int
    end_line: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    max_nesting_depth: int
    lines_of_code: int
    parameter_count: int


@dataclass
class FileMetrics:
    """Metrics for a single file."""
    path: str
    language: str
    lines_of_code: int
    function_count: int
    class_count: int
    avg_complexity: float
    max_complexity: int
    parse_success: bool
    functions: list[FunctionMetrics] = field(default_factory=list)


@dataclass
class RepoMetrics:
    """Aggregate metrics for the repository."""
    repository: str
    scan_time_ms: int
    summary: dict
    distribution: dict
    top_complex_functions: list[dict]
    files: list[FileMetrics] = field(default_factory=list)


class GitIgnoreFilter:
    """Filter files based on .gitignore patterns."""

    DEFAULT_PATTERNS = [
        ".git",
        ".git/",
        "__pycache__",
        "__pycache__/",
        "*.pyc",
        "node_modules",
        "node_modules/",
        ".DS_Store",
        "*.min.js",
        "*.bundle.js",
        "dist/",
        "build/",
        "vendor/",
        ".venv/",
        "venv/",
        "*.egg-info/",
    ]

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        patterns = list(self.DEFAULT_PATTERNS)

        gitignore_path = repo_root / ".gitignore"
        if gitignore_path.exists():
            patterns.extend(gitignore_path.read_text().splitlines())

        self.spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    def is_ignored(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        try:
            rel_path = path.relative_to(self.repo_root)
            return self.spec.match_file(str(rel_path))
        except ValueError:
            return False


def discover_files(repo_root: Path) -> list[Path]:
    """Discover source files respecting .gitignore."""
    gitignore = GitIgnoreFilter(repo_root)
    supported_extensions = {f".{lang}" if not lang.startswith(".") else lang
                           for lang in get_supported_languages()}
    # Map back to actual extensions
    from normalized_nodes import EXTENSION_TO_LANGUAGE
    supported_extensions = set(EXTENSION_TO_LANGUAGE.keys())

    files = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if gitignore.is_ignored(path):
            continue
        if path.suffix.lower() not in supported_extensions:
            continue
        # Skip binary files (simple heuristic)
        try:
            with open(path, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:
                    continue
        except (IOError, PermissionError):
            continue

        files.append(path)

    return files


def get_node_text(node, source_bytes: bytes) -> str:
    """Extract text for a node."""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def count_boolean_operators(node, source_bytes: bytes, language: str) -> int:
    """Count boolean operators in an expression."""
    operators = get_boolean_operators(language)
    if not operators:
        return 0

    count = 0

    def visit(n):
        nonlocal count
        if n.type == "binary_expression" or n.type == "boolean_operator":
            # Check if operator is && or ||
            for child in n.children:
                if child.type in ("&&", "||", "and", "or"):
                    count += 1
                elif hasattr(child, "text"):
                    text = get_node_text(child, source_bytes)
                    if text in operators:
                        count += 1

        for child in n.children:
            visit(child)

    visit(node)
    return count


def calculate_cyclomatic_complexity(function_node, source_bytes: bytes, language: str) -> int:
    """
    Calculate cyclomatic complexity for a function.

    Cyclomatic = 1 + decision_points + boolean_operators
    """
    complexity = 1

    def visit(node):
        nonlocal complexity

        if is_decision_point(node.type, language):
            complexity += 1

        # Count boolean operators (each && or || adds 1)
        if node.type in ("binary_expression", "boolean_operator"):
            ops = get_boolean_operators(language)
            for child in node.children:
                text = get_node_text(child, source_bytes)
                if text in ops:
                    complexity += 1

        for child in node.children:
            visit(child)

    visit(function_node)
    return complexity


def calculate_cognitive_complexity(function_node, source_bytes: bytes, language: str) -> int:
    """
    Calculate cognitive complexity with nesting penalty.

    Each decision point adds (1 + nesting_level) to complexity.
    """
    complexity = 0

    def visit(node, nesting_level: int):
        nonlocal complexity

        if is_decision_point(node.type, language):
            complexity += 1 + nesting_level

        # Determine if this node increases nesting
        increases_nesting = is_nesting_node(node.type, language)
        child_nesting = nesting_level + 1 if increases_nesting else nesting_level

        for child in node.children:
            visit(child, child_nesting)

    visit(function_node, 0)
    return complexity


def calculate_max_nesting_depth(function_node, language: str) -> int:
    """Calculate maximum nesting depth in a function."""
    max_depth = 0

    def visit(node, current_depth: int):
        nonlocal max_depth

        if is_nesting_node(node.type, language):
            current_depth += 1
            max_depth = max(max_depth, current_depth)

        for child in node.children:
            visit(child, current_depth)

    visit(function_node, 0)
    return max_depth


def get_function_name(function_node, source_bytes: bytes) -> str:
    """Extract function name from node."""
    # Try common child field names
    for field_name in ["name", "declarator"]:
        child = function_node.child_by_field_name(field_name)
        if child:
            # For declarators, dig deeper
            if child.type == "function_declarator":
                name_child = child.child_by_field_name("declarator")
                if name_child:
                    return get_node_text(name_child, source_bytes)
            return get_node_text(child, source_bytes)

    # Fallback: find identifier child
    for child in function_node.children:
        if child.type == "identifier":
            return get_node_text(child, source_bytes)

    return "<anonymous>"


def get_parameter_count(function_node, source_bytes: bytes) -> int:
    """Count function parameters."""
    params = function_node.child_by_field_name("parameters")
    if not params:
        return 0

    count = 0
    for child in params.children:
        if child.type in ("identifier", "typed_parameter", "parameter",
                          "formal_parameter", "required_parameter"):
            count += 1
        # Handle destructuring patterns
        elif child.type in ("object_pattern", "array_pattern"):
            count += 1

    return count


def analyze_file(file_path: Path, repo_root: Path) -> Optional[FileMetrics]:
    """Analyze a single file for complexity metrics."""
    language = get_language(str(file_path))
    if not language:
        return None

    try:
        content = file_path.read_bytes()
        source_text = content.decode("utf-8", errors="replace")
    except (IOError, PermissionError):
        return None

    try:
        parser = get_parser(language)
        tree = parser.parse(content)
    except Exception:
        # Parse failed
        return FileMetrics(
            path=str(file_path.relative_to(repo_root)),
            language=language,
            lines_of_code=source_text.count("\n") + 1,
            function_count=0,
            class_count=0,
            avg_complexity=0.0,
            max_complexity=0,
            parse_success=False,
        )

    functions: list[FunctionMetrics] = []
    class_count = 0

    def visit(node):
        nonlocal class_count

        if node.type in ("class_definition", "class_declaration"):
            class_count += 1

        if is_function_node(node.type, language):
            name = get_function_name(node, content)
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            cyclomatic = calculate_cyclomatic_complexity(node, content, language)
            cognitive = calculate_cognitive_complexity(node, content, language)
            max_nesting = calculate_max_nesting_depth(node, language)
            param_count = get_parameter_count(node, content)

            functions.append(FunctionMetrics(
                file=str(file_path.relative_to(repo_root)),
                name=name,
                line=start_line,
                end_line=end_line,
                cyclomatic_complexity=cyclomatic,
                cognitive_complexity=cognitive,
                max_nesting_depth=max_nesting,
                lines_of_code=end_line - start_line + 1,
                parameter_count=param_count,
            ))

        for child in node.children:
            visit(child)

    visit(tree.root_node)

    avg_complexity = (sum(f.cyclomatic_complexity for f in functions) / len(functions)
                      if functions else 0.0)
    max_complexity = max((f.cyclomatic_complexity for f in functions), default=0)

    return FileMetrics(
        path=str(file_path.relative_to(repo_root)),
        language=language,
        lines_of_code=source_text.count("\n") + 1,
        function_count=len(functions),
        class_count=class_count,
        avg_complexity=round(avg_complexity, 2),
        max_complexity=max_complexity,
        parse_success=True,
        functions=functions,
    )


def clone_or_update_repo(repo_url: str, cache_dir: str = "~/.cache/github") -> Path:
    """Clone or update a GitHub repository."""
    # Parse repo URL
    parts = repo_url.rstrip("/").split("/")
    owner = parts[-2]
    repo_name = parts[-1].replace(".git", "")

    cache_path = Path(cache_dir).expanduser() / owner / repo_name
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if (cache_path / ".git").exists():
        print(f"Updating existing repository: {cache_path}", file=sys.stderr)
        subprocess.run(["git", "pull", "--quiet"], cwd=cache_path, check=True)
    else:
        print(f"Cloning repository: {repo_url}", file=sys.stderr)
        subprocess.run(["git", "clone", "--quiet", repo_url, str(cache_path)], check=True)

    return cache_path


# Total CC bucket thresholds (based on benchmarks: axios=3.3K, fastapi=12.6K, codex=24K, react=152K)
BUCKET_SIMPLE_MAX = 5000       # Small focused libraries (< axios)
BUCKET_MEDIUM_MAX = 25000      # Medium frameworks (fastapi, codex range)
BUCKET_LARGE_MAX = 100000      # Large codebases
# Above BUCKET_LARGE_MAX = "complex" (massive codebases like React)


def get_complexity_bucket(total_cc: int) -> tuple[str, str]:
    """Map total cyclomatic complexity to bucket and description."""
    if total_cc < BUCKET_SIMPLE_MAX:
        return "simple", "Small, focused codebase - minimal documentation needed"
    elif total_cc < BUCKET_MEDIUM_MAX:
        return "medium", "Medium codebase - moderate documentation effort"
    elif total_cc < BUCKET_LARGE_MAX:
        return "large", "Large codebase - substantial documentation effort"
    else:
        return "complex", "Complex codebase - comprehensive documentation required"


def analyze_repository(repo_path: Path, repo_name: str, parallel: bool = True) -> RepoMetrics:
    """Analyze entire repository for complexity metrics."""
    start_time = time.time()

    print(f"Discovering files in {repo_path}...", file=sys.stderr)
    files = discover_files(repo_path)
    print(f"Found {len(files)} source files", file=sys.stderr)

    file_metrics: list[FileMetrics] = []

    if parallel and len(files) > 10:
        # Parallel processing for larger repos
        # Note: ProcessPoolExecutor requires picklable arguments
        # For simplicity, we'll use sequential processing
        # In production, we'd serialize file paths and repo_root
        pass

    # Sequential processing (simpler, still fast enough for most repos)
    for i, file_path in enumerate(files):
        if (i + 1) % 50 == 0:
            print(f"Processing file {i + 1}/{len(files)}...", file=sys.stderr)
        metrics = analyze_file(file_path, repo_path)
        if metrics:
            file_metrics.append(metrics)

    # Aggregate metrics
    all_functions = [f for fm in file_metrics for f in fm.functions]
    total_functions = len(all_functions)
    total_files = len(file_metrics)

    # Language breakdown
    languages: dict[str, int] = {}
    for fm in file_metrics:
        languages[fm.language] = languages.get(fm.language, 0) + 1

    # Complexity distribution
    low = sum(1 for f in all_functions if f.cyclomatic_complexity <= 5)
    medium = sum(1 for f in all_functions if 5 < f.cyclomatic_complexity <= 15)
    high = sum(1 for f in all_functions if f.cyclomatic_complexity > 15)

    # Total Cyclomatic Complexity (sum of all function CC)
    # This is the primary metric for documentation effort - scales with both size AND complexity
    total_cc = sum(f.cyclomatic_complexity for f in all_functions)

    # Average complexity per function (useful for code quality assessment)
    avg_complexity = total_cc / len(all_functions) if all_functions else 0.0

    bucket, description = get_complexity_bucket(total_cc)

    # Top complex functions
    top_functions = sorted(all_functions, key=lambda f: f.cyclomatic_complexity, reverse=True)[:10]
    top_complex = [
        {
            "file": f.file,
            "name": f.name,
            "line": f.line,
            "cyclomatic_complexity": f.cyclomatic_complexity,
            "cognitive_complexity": f.cognitive_complexity,
        }
        for f in top_functions
    ]

    scan_time_ms = int((time.time() - start_time) * 1000)

    return RepoMetrics(
        repository=repo_name,
        scan_time_ms=scan_time_ms,
        summary={
            "total_files": total_files,
            "total_functions": total_functions,
            "languages": languages,
            "total_cyclomatic_complexity": total_cc,
            "avg_cyclomatic_complexity": round(avg_complexity, 2),
            "complexity_bucket": bucket,
            "description": description,
            "parse_success_rate": round(
                sum(1 for fm in file_metrics if fm.parse_success) / total_files * 100
                if total_files else 0, 1
            ),
        },
        distribution={
            "low": low,
            "medium": medium,
            "high": high,
        },
        top_complex_functions=top_complex,
        files=file_metrics,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Analyze codebase complexity using tree-sitter AST parsing"
    )
    parser.add_argument(
        "--path",
        help="Local path to repository",
    )
    parser.add_argument(
        "--repo",
        help="GitHub repository URL (e.g., https://github.com/axios/axios)",
    )
    parser.add_argument(
        "--cache-dir",
        default="~/.cache/github",
        help="Directory for caching cloned repos",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--include-files",
        action="store_true",
        help="Include per-file metrics in output (verbose)",
    )

    args = parser.parse_args()

    if not args.path and not args.repo:
        parser.error("Either --path or --repo is required")

    # Resolve repository path
    if args.repo:
        repo_path = clone_or_update_repo(args.repo, args.cache_dir)
        repo_name = args.repo.rstrip("/").split("/")[-1].replace(".git", "")
    else:
        repo_path = Path(args.path).resolve()
        if not repo_path.exists():
            print(f"Error: Path not found: {repo_path}", file=sys.stderr)
            sys.exit(1)
        repo_name = repo_path.name

    # Analyze
    print(f"Analyzing {repo_name}...", file=sys.stderr)
    metrics = analyze_repository(repo_path, repo_name)

    # Prepare output
    output = {
        "repository": metrics.repository,
        "scan_time_ms": metrics.scan_time_ms,
        "summary": metrics.summary,
        "distribution": metrics.distribution,
        "top_complex_functions": metrics.top_complex_functions,
    }

    if args.include_files:
        output["files"] = [asdict(fm) for fm in metrics.files]

    # Output
    json_output = json.dumps(output, indent=2)

    if args.output:
        Path(args.output).write_text(json_output)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(json_output)

    # Summary to stderr
    print(f"\n=== Summary ===", file=sys.stderr)
    print(f"Repository: {metrics.repository}", file=sys.stderr)
    print(f"Scan time: {metrics.scan_time_ms}ms", file=sys.stderr)
    print(f"Total files: {metrics.summary['total_files']}", file=sys.stderr)
    print(f"Total functions: {metrics.summary['total_functions']}", file=sys.stderr)
    print(f"Languages: {metrics.summary['languages']}", file=sys.stderr)
    print(f"Total CC: {metrics.summary['total_cyclomatic_complexity']:,} ({metrics.summary['complexity_bucket']})", file=sys.stderr)
    print(f"Avg CC: {metrics.summary['avg_cyclomatic_complexity']}", file=sys.stderr)
    print(f"Distribution: Low={metrics.distribution['low']}, Medium={metrics.distribution['medium']}, High={metrics.distribution['high']}", file=sys.stderr)


if __name__ == "__main__":
    main()
