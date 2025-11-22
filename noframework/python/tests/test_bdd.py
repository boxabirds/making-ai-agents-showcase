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
    assert report.strip()
    # ensure citations parse
    tokens = []
    for line in report.splitlines():
        if "[" in line and "]" in line:
            tokens.extend([seg.strip("[]") for seg in line.split() if seg.startswith("[") and seg.endswith("]")])
    assert tokens, "Expected at least one citation token"
    for cit in tokens:
        path, start, end = validate_citation(cit)
        assert path and start >= 1 and end >= start
    store.close()
