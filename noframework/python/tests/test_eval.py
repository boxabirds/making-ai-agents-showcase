from pathlib import Path

from infinite_scalability.eval import evaluate_metrics
from infinite_scalability.orchestrator import run_pipeline
from infinite_scalability.store import Store


def test_evaluate_metrics(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    prompt = "Describe code"
    store = Store(persist=False)
    _, rv = run_pipeline(repo, prompt, store, gate=None)
    metrics = evaluate_metrics(store, rv.id, expected_items=1)  # type: ignore
    assert "support_rate" in metrics
    assert metrics["coverage"] >= 0.0
    assert "citation_veracity_rate" in metrics
    store.close()
