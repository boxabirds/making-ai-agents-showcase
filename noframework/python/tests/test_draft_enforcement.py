from pathlib import Path
import pytest

from infinite_scalability.orchestrator import run_pipeline
from infinite_scalability.store import Store
from infinite_scalability.enforcement import validate_report_citations, enforce_draft_citations
from infinite_scalability.ingest import ingest_repo


def test_draft_enforcement_and_validation(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    prompt = "Describe the code."
    store = Store(persist=False)
    report, rv = run_pipeline(repo, prompt, store, gate=None)
    # Validate every line has valid citation
    validate_report_citations(report, store)
    store.close()


def test_enforce_retrieves_aligned_citation(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    store = Store(persist=False)
    ingest_repo(repo, store)
    raw = "- foo returns one"
    repaired = enforce_draft_citations(raw, store, topic="foo")
    assert "code.py:" in repaired
    validate_report_citations(repaired, store)
    store.close()
