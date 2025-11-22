import numpy as np
from pathlib import Path

from infinite_scalability.ingest import ingest_repo
from infinite_scalability.retrieval import retrieve_context
from infinite_scalability.store import Store


def test_retrieve_context_hybrid_scoring(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("def special_function():\n    return 1\n")
    store = Store(persist=False)
    ingest_repo(repo, store)
    # get chunk embedding to use as query vector
    chunk = store.get_chunks_for_file(store.get_all_files()[0].id)[0]  # type: ignore
    vec = store.get_chunk_embedding(chunk.id)  # type: ignore
    ctx = retrieve_context(store, "special_function", query_vec=vec)
    assert ctx.chunks
    assert ctx.chunks[0].id == chunk.id
    store.close()
