from pathlib import Path

from infinite_scalability.orchestrator import run_pipeline
from infinite_scalability.store import Store


def test_run_pipeline(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    prompt = "Describe the code."
    store = Store(persist=False)
    report, rv = run_pipeline(repo, prompt, store)
    assert "foo" in report
    assert rv.coverage_score >= 0.0
    store.close()
