import numpy as np

from infinite_scalability.retrieval import retrieve_context
from infinite_scalability.ingest import ingest_repo
from infinite_scalability.store import Store
from pathlib import Path


def test_retrieve_context_embeddings_no_vectors(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("def foo():\n    return 123\n")
    store = Store(persist=False)
    ingest_repo(repo, store)
    ctx = retrieve_context(store, "foo", query_vec=np.zeros(1))
    assert ctx.chunks  # falls back to FTS
    store.close()
