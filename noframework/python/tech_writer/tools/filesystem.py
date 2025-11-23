"""
Filesystem exploration tools for the LLM agent.

Provides:
- list_files: Glob-based file listing with gitignore support
- read_file: Read file content with caching
"""

from pathlib import Path
from typing import Optional

import pathspec

from tech_writer.parser import detect_language
from tech_writer.store import CacheStore


def _load_gitignore(repo_root: Path) -> Optional[pathspec.PathSpec]:
    """Load .gitignore patterns from repo root."""
    gitignore_path = repo_root / ".gitignore"
    if not gitignore_path.exists():
        return None

    with open(gitignore_path, "r") as f:
        patterns = f.read().splitlines()

    # Add common patterns that should always be ignored
    patterns.extend([
        ".git/",
        ".git",
        "__pycache__/",
        "*.pyc",
        ".DS_Store",
    ])

    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def list_files(
    pattern: str = "*",
    path: str = ".",
    repo_root: Optional[Path] = None,
    respect_gitignore: bool = True,
) -> list[str]:
    """
    List files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "*.py", "src/**/*.ts")
        path: Directory to search in (relative to repo root)
        repo_root: Root of the repository
        respect_gitignore: Skip files in .gitignore

    Returns:
        List of file paths relative to repo root
    """
    if repo_root is None:
        repo_root = Path.cwd()
    else:
        repo_root = Path(repo_root)

    # Resolve the search path
    search_path = repo_root / path
    if not search_path.exists():
        return []

    # Load gitignore if needed
    gitignore_spec = None
    if respect_gitignore:
        gitignore_spec = _load_gitignore(repo_root)

    # Handle patterns
    # If pattern doesn't have **, we search only in the specified path
    if "**" in pattern:
        # Recursive glob from search path
        glob_pattern = pattern
    else:
        glob_pattern = pattern

    results = []
    try:
        for file_path in search_path.glob(glob_pattern):
            # Skip directories
            if file_path.is_dir():
                continue

            # Get path relative to repo root
            try:
                rel_path = file_path.relative_to(repo_root)
            except ValueError:
                continue

            rel_path_str = str(rel_path)

            # Check gitignore
            if gitignore_spec and gitignore_spec.match_file(rel_path_str):
                continue

            results.append(rel_path_str)
    except PermissionError:
        pass  # Skip directories we can't access

    return sorted(results)


def read_file(
    path: str,
    store: Optional[CacheStore] = None,
    repo_root: Optional[Path] = None,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> dict:
    """
    Read a file and cache its content.

    Args:
        path: File path relative to repo_root
        store: Cache store instance (if None, no caching)
        repo_root: Root of the repository
        start_line: Optional start line (1-indexed)
        end_line: Optional end line (inclusive)

    Returns:
        Dict with keys: path, content, language, line_count

    Side effects:
        Caches full content in store (even if line range requested)
    """
    from binaryornot.check import is_binary

    if repo_root is None:
        repo_root = Path.cwd()
    else:
        repo_root = Path(repo_root)

    full_path = repo_root / path

    # Check file exists
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Check if file is binary
    if is_binary(str(full_path)):
        raise ValueError(f"Cannot read binary file: {path}")

    # Check cache first
    if store is not None:
        cached = store.get_file(path)
        if cached is not None:
            content = cached.content
            language = cached.language
            line_count = cached.line_count

            # Handle line range
            if start_line is not None or end_line is not None:
                lines = content.splitlines()
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else len(lines)
                content = "\n".join(lines[start_idx:end_idx])

            return {
                "path": path,
                "content": content,
                "language": language,
                "line_count": line_count,
            }

    # Read file content
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            full_content = f.read()
    except Exception as e:
        raise IOError(f"Failed to read file {path}: {e}")

    language = detect_language(path) or "text"
    line_count = full_content.count("\n") + 1 if full_content else 0

    # Cache full content
    if store is not None:
        store.add_file(path, full_content, language)

    # Handle line range for return value
    content = full_content
    if start_line is not None or end_line is not None:
        lines = full_content.splitlines()
        start_idx = (start_line - 1) if start_line else 0
        end_idx = end_line if end_line else len(lines)
        content = "\n".join(lines[start_idx:end_idx])

    return {
        "path": path,
        "content": content,
        "language": language,
        "line_count": line_count,
    }
