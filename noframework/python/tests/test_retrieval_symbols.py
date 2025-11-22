from pathlib import Path

from infinite_scalability.ingest import ingest_repo
from infinite_scalability.retrieval import retrieve_context
from infinite_scalability.store import Store


def test_retrieve_context_symbol_chunks(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("def special_function():\n    return 1\n")
    store = Store(persist=False)
    ingest_repo(repo, store)
    ctx = retrieve_context(store, "special_function")
    assert any("special_function" in c.text for c in ctx.chunks)
    store.close()
