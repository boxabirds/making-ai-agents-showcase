"""
End-to-end integration tests for tech_writer.

These tests run the full pipeline against a fixture repository.
They require OPENAI_API_KEY (from .env.test or environment).

API key handling:
- If .env.test exists, it's loaded automatically by tests/__init__.py
- If API key is available, tests run
- If API key is missing and SKIP_E2E_TESTS is not set, tests FAIL explicitly
- To skip in CI without API access, set SKIP_E2E_TESTS=1
"""

import os
import subprocess
import pytest
from pathlib import Path

from tech_writer.orchestrator import run_pipeline
from tech_writer.citations import verify_all_citations, extract_citations


FIXTURE_REPO = Path(__file__).parent.parent / "fixtures" / "sample_flask_app"

# Check for API key availability
HAS_API_KEY = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY"))
SKIP_E2E_REQUESTED = os.environ.get("SKIP_E2E_TESTS", "").lower() in ("1", "true", "yes")


def _check_api_key_or_fail():
    """Check API key availability and fail explicitly if missing."""
    if SKIP_E2E_REQUESTED:
        if HAS_API_KEY:
            pytest.skip(
                "SKIP_E2E_TESTS=1 but API key is available. "
                "Unset SKIP_E2E_TESTS to run these tests."
            )
        else:
            pytest.skip("E2E tests skipped via SKIP_E2E_TESTS env var")
    elif not HAS_API_KEY:
        pytest.fail(
            "OPENAI_API_KEY or OPENROUTER_API_KEY required for e2e tests. "
            "Either provide .env.test with API keys, set env vars, "
            "or set SKIP_E2E_TESTS=1 to explicitly skip."
        )


@pytest.fixture
def fixture_repo():
    """Path to the fixture Flask app."""
    _check_api_key_or_fail()
    assert FIXTURE_REPO.exists(), f"Fixture repo not found: {FIXTURE_REPO}"
    return FIXTURE_REPO


class TestE2EPipeline:
    """End-to-end pipeline tests."""

    def test_full_pipeline_produces_report(self, fixture_repo):
        """Test that the pipeline produces a non-empty report."""
        prompt = "Document the API endpoints in this Flask application."

        report, store, _cost = run_pipeline(
            prompt=prompt,
            repo=str(fixture_repo),
            max_exploration=20,
            max_sections=5,
        )

        assert report, "Report should not be empty"
        assert len(report) > 100, "Report should have substantial content"
        assert store.list_cached_files(), "Some files should be cached"

    def test_report_has_citations(self, fixture_repo):
        """Test that the report contains citations."""
        prompt = "Explain how the routes are organized."

        report, store, _cost = run_pipeline(
            prompt=prompt,
            repo=str(fixture_repo),
            max_exploration=15,
            max_sections=3,
        )

        citations = extract_citations(report)
        assert len(citations) > 0, "Report should contain citations"

    def test_citations_are_mostly_valid(self, fixture_repo):
        """Test that citations reference cached files with valid line ranges."""
        prompt = "Document the data models."

        report, store, _cost = run_pipeline(
            prompt=prompt,
            repo=str(fixture_repo),
            max_exploration=15,
            max_sections=3,
        )

        results, valid, invalid = verify_all_citations(report, store)

        # Allow some invalid citations but majority should be valid
        total = valid + invalid
        if total > 0:
            validity_rate = valid / total
            assert validity_rate >= 0.5, f"Citation validity too low: {validity_rate:.0%} ({valid}/{total})"

    def test_exploration_respects_max_steps(self, fixture_repo):
        """Test that exploration is limited."""
        prompt = "Document everything in extreme detail."

        report, store, _cost = run_pipeline(
            prompt=prompt,
            repo=str(fixture_repo),
            max_exploration=5,  # Very low limit
            max_sections=2,
        )

        # With only 5 exploration steps, we shouldn't read too many files
        cached_files = store.list_cached_files()
        # The limit is soft (tool calls, not files), but should still constrain
        assert len(cached_files) <= 15, f"Too many files cached: {len(cached_files)}"

    def test_max_sections_respected(self, fixture_repo):
        """Test that outline is truncated to max_sections."""
        prompt = "Create comprehensive documentation covering every aspect."

        report, store, _cost = run_pipeline(
            prompt=prompt,
            repo=str(fixture_repo),
            max_exploration=10,
            max_sections=2,
        )

        # Count top-level sections (## headers)
        section_count = report.count("\n## ")
        assert section_count <= 3, f"Too many sections: {section_count}"  # Allow some flexibility


class TestE2ECLIIntegration:
    """Test CLI integration."""

    def test_cli_produces_output(self, fixture_repo, tmp_path):
        """Test that CLI produces output file."""
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("List the main components of this Flask app.")

        output_file = tmp_path / "report.md"

        result = subprocess.run(
            [
                "python", "-m", "tech_writer",
                "--prompt", str(prompt_file),
                "--repo", str(fixture_repo),
                "--output", str(output_file),
                "--max-exploration", "10",
                "--max-sections", "3",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_file.exists(), "Output file should be created"
        content = output_file.read_text()
        assert len(content) > 0, "Output file should not be empty"

    def test_cli_verify_citations(self, fixture_repo, tmp_path):
        """Test that --verify-citations flag works."""
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("Document the routes.")

        result = subprocess.run(
            [
                "python", "-m", "tech_writer",
                "--prompt", str(prompt_file),
                "--repo", str(fixture_repo),
                "--verify-citations",
                "--max-exploration", "10",
                "--max-sections", "2",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        # Citation stats should be in stderr
        assert "Citation" in result.stderr or "citation" in result.stderr.lower()

    def test_cli_persist_cache(self, fixture_repo, tmp_path):
        """Test that --persist-cache creates a cache file."""
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("Document the app.")

        cache_file = tmp_path / "test_cache.db"

        result = subprocess.run(
            [
                "python", "-m", "tech_writer",
                "--prompt", str(prompt_file),
                "--repo", str(fixture_repo),
                "--persist-cache",
                "--cache-path", str(cache_file),
                "--max-exploration", "5",
                "--max-sections", "2",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert cache_file.exists(), "Cache file should be created"

    def test_cli_help(self):
        """Test that --help shows new options."""
        result = subprocess.run(
            ["python", "-m", "tech_writer", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--max-exploration" in result.stdout
        assert "--max-sections" in result.stdout
        assert "--persist-cache" in result.stdout
        assert "--cache-path" in result.stdout


class TestFTS5Search:
    """Test FTS5 full-text search."""

    def test_fts5_search_basic(self):
        """Test basic FTS5 search functionality."""
        from tech_writer.store import CacheStore

        store = CacheStore()
        store.add_file("test.py", "def hello_world():\n    print('hello')\n", "python")
        store.add_file("other.py", "def goodbye():\n    pass\n", "python")

        results = store.search("hello")
        assert len(results) > 0
        assert any("test.py" in r["path"] for r in results)

    def test_fts5_search_special_chars(self):
        """Test FTS5 handles special characters."""
        from tech_writer.store import CacheStore

        store = CacheStore()
        store.add_file("config.py", "DATABASE_URL = 'postgres://user:pass@host'\n", "python")

        # Should not crash on special chars
        results = store.search("user:pass")
        assert isinstance(results, list)

    def test_fts5_search_empty_query(self):
        """Test FTS5 handles empty query."""
        from tech_writer.store import CacheStore

        store = CacheStore()
        store.add_file("test.py", "content", "python")

        results = store.search("")
        assert results == []

        results = store.search("   ")
        assert results == []

    def test_fts5_search_limit(self):
        """Test FTS5 respects limit."""
        from tech_writer.store import CacheStore

        store = CacheStore()
        # Add many files with "def"
        for i in range(20):
            store.add_file(f"file{i}.py", f"def func{i}():\n    pass\n", "python")

        results = store.search("def", limit=5)
        assert len(results) <= 5
