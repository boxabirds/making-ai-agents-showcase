"""
Core tests for tech_writer module.

Tests store, filesystem tools, semantic tools, and citations.
"""

import pytest
from pathlib import Path

from tech_writer.store import CacheStore, Symbol
from tech_writer.tools.filesystem import list_files, read_file
from tech_writer.tools.semantic import (
    get_symbols, get_imports, get_definition,
    get_references, get_structure, search_text
)
from tech_writer.citations import (
    parse_citation, extract_citations, verify_citation,
    verify_all_citations, Citation
)
from tech_writer.parser import ParserManager, detect_language, is_supported


class TestCacheStore:
    """Tests for SQLite cache store."""

    def test_add_and_get_file(self, store):
        """Test adding and retrieving a file."""
        file_id = store.add_file("src/main.py", "print('hello')", "python")
        assert file_id > 0

        record = store.get_file("src/main.py")
        assert record is not None
        assert record.path == "src/main.py"
        assert record.content == "print('hello')"
        assert record.language == "python"

    def test_add_file_idempotent(self, store):
        """Test that add_file returns same ID for same path."""
        id1 = store.add_file("src/main.py", "v1", "python")
        id2 = store.add_file("src/main.py", "v2", "python")
        assert id1 == id2

        # Content should be updated
        record = store.get_file("src/main.py")
        assert record.content == "v2"

    def test_has_file(self, store):
        """Test checking if file exists."""
        assert not store.has_file("test.py")
        store.add_file("test.py", "content", "python")
        assert store.has_file("test.py")

    def test_symbols(self, store):
        """Test symbol storage and retrieval."""
        file_id = store.add_file("src/main.py", "def foo(): pass", "python")
        store.add_symbols(file_id, [
            Symbol(name="foo", kind="function", line=1),
            Symbol(name="Bar", kind="class", line=5, end_line=10),
        ])

        symbols = store.get_symbols(file_id)
        assert len(symbols) == 2
        assert symbols[0].name == "foo"
        assert symbols[1].name == "Bar"

    def test_get_symbols_by_name(self, store):
        """Test finding symbols by name."""
        file_id = store.add_file("src/main.py", "class Foo: pass", "python")
        store.add_symbols(file_id, [
            Symbol(name="Foo", kind="class", line=1),
        ])

        symbols = store.get_symbols_by_name("Foo")
        assert len(symbols) == 1
        assert symbols[0].kind == "class"

    def test_list_cached_files(self, store):
        """Test listing cached files."""
        store.add_file("a.py", "a", "python")
        store.add_file("b.py", "b", "python")
        store.add_file("c.py", "c", "python")

        files = store.list_cached_files()
        assert len(files) == 3
        assert "a.py" in files


class TestListFiles:
    """Tests for list_files tool."""

    def test_list_all_files(self, sample_repo):
        """Test listing all files."""
        files = list_files("**/*", repo_root=sample_repo)
        assert len(files) > 0
        assert any("main.py" in f for f in files)

    def test_list_python_files(self, sample_repo):
        """Test listing Python files."""
        files = list_files("**/*.py", repo_root=sample_repo)
        assert all(f.endswith(".py") for f in files)

    def test_list_in_subdirectory(self, sample_repo):
        """Test listing files in subdirectory."""
        files = list_files("*.py", path="lib", repo_root=sample_repo)
        assert all(f.startswith("lib/") for f in files)

    def test_nonexistent_directory(self, sample_repo):
        """Test listing in nonexistent directory returns empty."""
        files = list_files("*.py", path="nonexistent", repo_root=sample_repo)
        assert files == []

    def test_respects_gitignore(self, sample_repo):
        """Test that gitignored files are excluded."""
        # Create a file that would be gitignored
        (sample_repo / "__pycache__").mkdir()
        (sample_repo / "__pycache__" / "test.pyc").write_text("")

        files = list_files("**/*", repo_root=sample_repo, respect_gitignore=True)
        assert not any("__pycache__" in f for f in files)


class TestReadFile:
    """Tests for read_file tool."""

    def test_read_entire_file(self, sample_repo, store):
        """Test reading entire file."""
        result = read_file("main.py", store=store, repo_root=sample_repo)
        assert result["path"] == "main.py"
        assert "def main" in result["content"]
        assert result["language"] == "python"

    def test_read_line_range(self, sample_repo, store):
        """Test reading specific line range."""
        result = read_file("main.py", store=store, repo_root=sample_repo,
                          start_line=1, end_line=3)
        lines = result["content"].splitlines()
        assert len(lines) == 3

    def test_file_cached(self, sample_repo, store):
        """Test that file is cached after reading."""
        read_file("main.py", store=store, repo_root=sample_repo)
        assert store.has_file("main.py")

    def test_read_from_cache(self, sample_repo, store):
        """Test reading from cache."""
        # First read
        read_file("main.py", store=store, repo_root=sample_repo)

        # Second read should use cache
        result = read_file("main.py", store=store, repo_root=sample_repo)
        assert result["content"] is not None

    def test_nonexistent_file(self, sample_repo, store):
        """Test reading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            read_file("nonexistent.py", store=store, repo_root=sample_repo)


class TestParser:
    """Tests for tree-sitter parser."""

    def test_detect_language(self):
        """Test language detection from extension."""
        assert detect_language("main.py") == "python"
        assert detect_language("app.js") == "javascript"
        assert detect_language("index.ts") == "typescript"
        assert detect_language("main.go") == "go"
        assert detect_language("unknown.xyz") is None

    def test_is_supported(self):
        """Test checking if language is supported."""
        assert is_supported("python")
        assert is_supported("javascript")
        assert not is_supported("unknown")

    def test_extract_python_symbols(self):
        """Test extracting symbols from Python."""
        pm = ParserManager()
        code = '''
class Foo:
    def bar(self):
        pass

def baz():
    pass
'''
        symbols = pm.extract_symbols(code, "python")
        names = [s["name"] for s in symbols]
        assert "Foo" in names
        assert "bar" in names
        assert "baz" in names

    def test_extract_javascript_symbols(self):
        """Test extracting symbols from JavaScript."""
        pm = ParserManager()
        code = '''
function add(a, b) {
    return a + b;
}

class Calculator {
    multiply(x, y) {
        return x * y;
    }
}
'''
        symbols = pm.extract_symbols(code, "javascript")
        names = [s["name"] for s in symbols]
        assert "add" in names
        assert "Calculator" in names
        assert "multiply" in names

    def test_extract_python_imports(self):
        """Test extracting imports from Python."""
        pm = ParserManager()
        code = '''
import os
from pathlib import Path
from collections import defaultdict, Counter
'''
        imports = pm.extract_imports(code, "python")
        modules = [i["module"] for i in imports]
        assert "os" in modules
        assert "pathlib" in modules
        assert "collections" in modules


class TestSemanticTools:
    """Tests for semantic query tools."""

    def test_get_symbols(self, sample_repo, store):
        """Test get_symbols tool."""
        read_file("lib/utils.py", store=store, repo_root=sample_repo)
        symbols = get_symbols("lib/utils.py", store=store, repo_root=sample_repo)

        names = [s["name"] for s in symbols]
        assert "Helper" in names
        assert "format_path" in names

    def test_get_symbols_filtered(self, sample_repo, store):
        """Test get_symbols with kind filter."""
        read_file("lib/utils.py", store=store, repo_root=sample_repo)
        symbols = get_symbols("lib/utils.py", kind="class", store=store, repo_root=sample_repo)

        assert all(s["kind"] == "class" for s in symbols)

    def test_get_imports(self, sample_repo, store):
        """Test get_imports tool."""
        read_file("lib/utils.py", store=store, repo_root=sample_repo)
        imports = get_imports("lib/utils.py", store=store, repo_root=sample_repo)

        modules = [i["module"] for i in imports]
        assert "os" in modules
        assert "pathlib" in modules

    def test_get_definition(self, sample_repo, store):
        """Test get_definition tool."""
        read_file("lib/utils.py", store=store, repo_root=sample_repo)
        get_symbols("lib/utils.py", store=store, repo_root=sample_repo)

        defn = get_definition("Helper", store=store)
        assert defn is not None
        assert defn["kind"] == "class"

    def test_get_references(self, sample_repo, store):
        """Test get_references tool."""
        read_file("lib/utils.py", store=store, repo_root=sample_repo)

        refs = get_references("Path", store=store)
        assert len(refs) > 0
        assert any("lib/utils.py" in r["path"] for r in refs)

    def test_get_structure(self, sample_repo, store):
        """Test get_structure tool."""
        read_file("lib/utils.py", store=store, repo_root=sample_repo)
        struct = get_structure("lib/utils.py", store=store, repo_root=sample_repo)

        assert "imports" in struct
        assert "classes" in struct
        assert "functions" in struct
        assert len(struct["classes"]) > 0

    def test_search_text(self, sample_repo, store):
        """Test search_text tool."""
        read_file("lib/utils.py", store=store, repo_root=sample_repo)
        read_file("main.py", store=store, repo_root=sample_repo)

        results = search_text("def", store=store)
        assert len(results) > 0


class TestCitations:
    """Tests for citation parsing and verification."""

    def test_parse_valid_citation(self):
        """Test parsing valid citation."""
        cit = parse_citation("src/main.py:10-25")
        assert cit.path == "src/main.py"
        assert cit.start_line == 10
        assert cit.end_line == 25

    def test_parse_nested_path(self):
        """Test parsing citation with nested path."""
        cit = parse_citation("lib/core/Axios.js:100-150")
        assert cit.path == "lib/core/Axios.js"

    def test_parse_single_line(self):
        """Test parsing single-line citation."""
        cit = parse_citation("main.py:5-5")
        assert cit.start_line == cit.end_line

    def test_parse_invalid_missing_end(self):
        """Test parsing invalid citation (missing end line)."""
        with pytest.raises(ValueError):
            parse_citation("main.py:10")

    def test_parse_invalid_non_numeric(self):
        """Test parsing invalid citation (non-numeric)."""
        with pytest.raises(ValueError):
            parse_citation("main.py:abc-def")

    def test_extract_citations(self):
        """Test extracting citations from markdown."""
        markdown = '''
The main class [lib/axios.js:10-20] provides
HTTP methods [lib/axios.js:30-40] for requests.
'''
        citations = extract_citations(markdown)
        assert len(citations) == 2
        assert citations[0].path == "lib/axios.js"
        assert citations[1].start_line == 30

    def test_verify_valid_citation(self, store):
        """Test verifying valid citation."""
        store.add_file("test.py", "line1\nline2\nline3\nline4\nline5", "python")
        cit = Citation(path="test.py", start_line=2, end_line=4)

        result = verify_citation(cit, store)
        assert result.valid
        assert result.content == "line2\nline3\nline4"

    def test_verify_file_not_cached(self, store):
        """Test verifying citation for uncached file."""
        cit = Citation(path="unknown.py", start_line=1, end_line=5)

        result = verify_citation(cit, store)
        assert not result.valid
        assert "not found" in result.error

    def test_verify_out_of_range(self, store):
        """Test verifying citation with out-of-range lines."""
        store.add_file("test.py", "line1\nline2\nline3", "python")
        cit = Citation(path="test.py", start_line=10, end_line=20)

        result = verify_citation(cit, store)
        assert not result.valid
        assert "out of range" in result.error

    def test_verify_all_citations(self, store):
        """Test verifying all citations in document."""
        store.add_file("a.py", "line1\nline2\nline3", "python")
        store.add_file("b.py", "code1\ncode2", "python")

        markdown = '''
See [a.py:1-2] and [b.py:1-1] for details.
Also [unknown.py:1-5] which doesn't exist.
'''
        results, valid, invalid = verify_all_citations(markdown, store)

        assert len(results) == 3
        assert valid == 2
        assert invalid == 1
