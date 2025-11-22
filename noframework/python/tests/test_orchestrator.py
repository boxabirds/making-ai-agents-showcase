from pathlib import Path

from infinite_scalability.orchestrator import run_pipeline
from infinite_scalability.store import Store
from infinite_scalability.enforcement import validate_report_citations


def test_run_pipeline(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    prompt = "Describe the code."
    store = Store(persist=False)
    report, rv = run_pipeline(repo, prompt, store)
    assert report.strip()
    assert "[" in report  # citations included
    validate_report_citations(report, store)
    assert rv.coverage_score >= 0.0
    store.close()
