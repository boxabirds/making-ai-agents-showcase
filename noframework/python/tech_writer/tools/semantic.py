"""
Semantic query tools for the LLM agent.

Provides tree-sitter powered queries:
- get_symbols: Extract functions, classes, methods
- get_imports: Extract import statements
- get_definition: Find where a symbol is defined
- get_references: Find all usages of a symbol
- get_structure: Get structural overview of a file
- search_text: Full-text search across cached files
"""

import re
from pathlib import Path
from typing import Optional

from tech_writer.parser import ParserManager, detect_language
from tech_writer.store import CacheStore, Symbol


# Global parser manager (reused across calls)
_parser_manager: Optional[ParserManager] = None


def _get_parser_manager() -> ParserManager:
    """Get or create global parser manager."""
    global _parser_manager
    if _parser_manager is None:
        _parser_manager = ParserManager()
    return _parser_manager


def get_symbols(
    path: str,
    kind: Optional[str] = None,
    store: Optional[CacheStore] = None,
    repo_root: Optional[Path] = None,
) -> list[dict]:
    """
    Get symbols defined in a file.

    Args:
        path: File path
        kind: Filter by kind ("function", "class", "method")
        store: Cache store
        repo_root: Repository root

    Returns:
        List of dicts: {name, kind, line, end_line, signature}
    """
    # Get file content from cache or read from disk
    content = None
    language = None

    if store is not None:
        cached = store.get_file(path)
        if cached:
            content = cached.content
            language = cached.language

    if content is None and repo_root is not None:
        # Read from disk
        full_path = Path(repo_root) / path
        if full_path.exists():
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            language = detect_language(path)

    if content is None:
        return []

    pm = _get_parser_manager()
    symbols = pm.extract_symbols(content, language or "")

    # Filter by kind if specified
    if kind:
        symbols = [s for s in symbols if s["kind"] == kind]

    # Also store symbols in cache if we have a store
    if store is not None:
        cached = store.get_file(path)
        if cached:
            # Convert dicts to Symbol objects
            sym_objects = [
                Symbol(
                    name=s["name"],
                    kind=s["kind"],
                    line=s["line"],
                    end_line=s.get("end_line"),
                    signature=s.get("signature"),
                    doc=s.get("doc"),
                )
                for s in symbols
            ]
            store.add_symbols(cached.id, sym_objects)

    return symbols


def get_imports(
    path: str,
    store: Optional[CacheStore] = None,
    repo_root: Optional[Path] = None,
) -> list[dict]:
    """
    Get imports in a file.

    Args:
        path: File path
        store: Cache store
        repo_root: Repository root

    Returns:
        List of dicts: {module, alias, is_relative, line}
    """
    content = None
    language = None

    if store is not None:
        cached = store.get_file(path)
        if cached:
            content = cached.content
            language = cached.language

    if content is None and repo_root is not None:
        full_path = Path(repo_root) / path
        if full_path.exists():
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            language = detect_language(path)

    if content is None:
        return []

    pm = _get_parser_manager()
    return pm.extract_imports(content, language or "")


def get_definition(
    name: str,
    store: Optional[CacheStore] = None,
) -> Optional[dict]:
    """
    Find where a symbol is defined.

    Args:
        name: Symbol name to find
        store: Cache store (searches cached files only)

    Returns:
        Dict: {path, line, end_line, kind, signature} or None
    """
    if store is None:
        return None

    # Search through all cached symbols
    symbols = store.get_symbols_by_name(name)
    if not symbols:
        return None

    # Return the first definition (prefer classes/functions over methods)
    for sym in symbols:
        if sym.kind in ("class", "function", "type"):
            return {
                "path": sym.file_path,
                "line": sym.line,
                "end_line": sym.end_line,
                "kind": sym.kind,
                "signature": sym.signature,
            }

    # Fall back to first found
    sym = symbols[0]
    return {
        "path": sym.file_path,
        "line": sym.line,
        "end_line": sym.end_line,
        "kind": sym.kind,
        "signature": sym.signature,
    }


def get_references(
    name: str,
    store: Optional[CacheStore] = None,
) -> list[dict]:
    """
    Find all usages of a symbol.

    Args:
        name: Symbol name to find
        store: Cache store (searches cached files only)

    Returns:
        List of dicts: {path, line, context}
    """
    if store is None:
        return []

    references = []

    # Search through all cached files
    for file_path in store.list_cached_files():
        cached = store.get_file(file_path)
        if cached is None:
            continue

        content = cached.content
        lines = content.splitlines()

        # Simple text search for the name
        # Use word boundaries to avoid partial matches
        pattern = re.compile(r'\b' + re.escape(name) + r'\b')

        for i, line in enumerate(lines):
            if pattern.search(line):
                references.append({
                    "path": file_path,
                    "line": i + 1,
                    "context": line.strip(),
                })

    return references


def get_structure(
    path: str,
    store: Optional[CacheStore] = None,
    repo_root: Optional[Path] = None,
) -> dict:
    """
    Get structural overview of a file.

    Args:
        path: File path
        store: Cache store
        repo_root: Repository root

    Returns:
        Dict: {imports: [...], classes: [...], functions: [...]}
    """
    symbols = get_symbols(path, store=store, repo_root=repo_root)
    imports = get_imports(path, store=store, repo_root=repo_root)

    # Organize symbols by kind
    classes = []
    functions = []

    for sym in symbols:
        if sym["kind"] == "class":
            # Find methods belonging to this class
            methods = [s for s in symbols if s.get("parent") == sym["name"]]
            classes.append({
                "name": sym["name"],
                "line": sym["line"],
                "end_line": sym.get("end_line"),
                "methods": [
                    {
                        "name": m["name"],
                        "line": m["line"],
                        "signature": m.get("signature"),
                    }
                    for m in methods
                ],
            })
        elif sym["kind"] == "function":
            functions.append({
                "name": sym["name"],
                "line": sym["line"],
                "end_line": sym.get("end_line"),
                "signature": sym.get("signature"),
            })

    return {
        "imports": imports,
        "classes": classes,
        "functions": functions,
    }


def search_text(
    query: str,
    store: CacheStore,
    limit: int = 20,
) -> list[dict]:
    """
    Full-text search across cached files.

    Args:
        query: Search query
        store: Cache store
        limit: Max results

    Returns:
        List of dicts: {path, line, snippet, score}
    """
    results = []

    # Simple text search (not FTS5 yet - that's an enhancement)
    # Use word boundaries for better matching
    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error:
        # Invalid regex, treat as literal
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    for file_path in store.list_cached_files():
        cached = store.get_file(file_path)
        if cached is None:
            continue

        content = cached.content
        lines = content.splitlines()

        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                results.append({
                    "path": file_path,
                    "line": i + 1,
                    "snippet": line.strip()[:200],
                    "score": 1.0,  # Simple scoring
                })

                if len(results) >= limit:
                    return results

    return results
