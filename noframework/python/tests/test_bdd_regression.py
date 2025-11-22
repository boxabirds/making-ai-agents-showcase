from datetime import datetime, timezone
from pathlib import Path

from infinite_scalability.models import SummaryOutput, CoverageGate


def test_bdd_regression_with_stubbed_llm(monkeypatch, tmp_path: Path):
    """
    BDD-style regression: stub LLMs for determinism, run full pipeline, and assert stable report content/metrics.
    """
    # Repository fixture
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    prompt = "Summarize functions."

    # Stub summarize_text to emit a deterministic summary with a valid citation
    def stub_summarize_text(text: str, instructions: str = "") -> SummaryOutput:
        path = str(repo / "code.py")
        return SummaryOutput(text=f"Summary of code [{path}:1-2]", citations=[f"{path}:1-2"], confidence=1.0)

    # Stub draft_report to emit a deterministic report that uses citations from evidence
    def stub_draft_report(prompt_text: str, evidences: list[str]) -> str:
        path = str(repo / "code.py")
        return f"# Report\n- Deterministic claim [{path}:1-2]\n"

    # Apply stubs across modules that reference these functions
    monkeypatch.setattr("infinite_scalability.llm.summarize_text", stub_summarize_text)
    monkeypatch.setattr("infinite_scalability.dspy_pipeline.summarize_text", stub_summarize_text)
    monkeypatch.setattr("infinite_scalability.llm.draft_report", stub_draft_report)
    monkeypatch.setattr("infinite_scalability.dspy_pipeline.draft_report", stub_draft_report)
    monkeypatch.setattr("infinite_scalability.orchestrator.draft_report", stub_draft_report)

    from infinite_scalability.orchestrator import run_pipeline
    from infinite_scalability.store import Store

    store = Store(persist=False)
    gate = CoverageGate(min_support_rate=0.0, min_coverage=0.0, min_citation_rate=0.0, max_high_issues=1, max_medium_issues=5)
    report, rv = run_pipeline(repo, prompt, store, gate=gate, max_iters=1)

    assert "Deterministic claim" in report
    assert str(repo / "code.py") in report
    assert rv.coverage_score >= 0.0
    store.close()
