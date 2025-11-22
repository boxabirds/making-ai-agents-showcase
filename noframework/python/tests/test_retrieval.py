from pathlib import Path

from infinite_scalability.ingest import ingest_repo
from infinite_scalability.retrieval import retrieve_context
from infinite_scalability.store import Store


def test_retrieve_context(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("def foo():\n    return 123\n")
    store = Store(persist=False)
    ingest_repo(repo, store)
    ctx = retrieve_context(store, "foo")
    assert any("foo" in c.text for c in ctx.chunks)
    store.close()
