from pathlib import Path
import pytest

from infinite_scalability.orchestrator import run_pipeline
from infinite_scalability.store import Store
from infinite_scalability.enforcement import validate_report_citations


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
