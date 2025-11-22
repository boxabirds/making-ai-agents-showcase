from pathlib import Path

from infinite_scalability.ingest import ingest_repo
from infinite_scalability.store import Store


def test_ingest_basic(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Title\n\nParagraph one.\n\nParagraph two.")
    (repo / "code.py").write_text("def foo():\n    return 42\n")

    store = Store(persist=False)
    ingest_repo(repo, store)

    # should have two files
    cur = store.conn.execute("SELECT COUNT(*) FROM files")
    assert cur.fetchone()[0] == 2

    cur = store.conn.execute("SELECT COUNT(*) FROM chunks")
    chunk_count = cur.fetchone()[0]
    assert chunk_count >= 2  # doc paragraphs + code block

    # FTS search should find text
    chunks = store.search_chunks_fts("Paragraph")
    assert len(chunks) >= 1
    store.close()
