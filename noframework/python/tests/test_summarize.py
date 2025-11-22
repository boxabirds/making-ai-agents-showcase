from pathlib import Path

from infinite_scalability.ingest import ingest_repo
from infinite_scalability.store import Store
from infinite_scalability.summarize import summarize_all_files


def test_summarize_all_files(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 42\n")
    store = Store(persist=False)
    ingest_repo(repo, store)
    summaries = summarize_all_files(store)
    assert len(summaries) == 1
    assert "foo" in summaries[0].text
    store.close()
