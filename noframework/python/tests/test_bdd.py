from pathlib import Path

from infinite_scalability.orchestrator import run_pipeline
from infinite_scalability.store import Store
from infinite_scalability.citations import validate_citation


def test_bdd_full_pipeline(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    prompt = "Describe the code."
    store = Store(persist=False)
    report, rv = run_pipeline(repo, prompt, store, gate=None)
    assert "Citations" in report
    # ensure citations parse
    lines = [l for l in report.splitlines() if l.startswith("- [") and "]" in l]
    for line in lines:
        cit = line.split("[", 1)[1].split("]", 1)[0]
        path, start, end = validate_citation(cit)
        assert path and start >= 1 and end >= start
    store.close()
