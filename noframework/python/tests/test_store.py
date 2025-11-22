import sqlite3
from pathlib import Path

import pytest

from infinite_scalability.store import Store
from infinite_scalability.schema import init_db


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    )
    return cur.fetchone() is not None


def test_store_lifecycle_ephemeral(tmp_path: Path):
    store = Store(persist=False)
    db_path = store.db_path
    assert db_path.exists()
    store.close()
    assert not db_path.exists()


def test_store_lifecycle_persist(tmp_path: Path):
    db_path = tmp_path / "store.db"
    store = Store(db_path=db_path, persist=True)
    assert db_path.exists()
    store.close()
    assert db_path.exists()


def test_schema_created():
    store = Store(persist=False)
    conn = store.conn
    # tables
    for table in [
        "files",
        "chunks",
        "symbols",
        "edges",
        "summaries",
        "report_versions",
        "claims",
        "chunk_embeddings",
        "symbol_embeddings",
        "chunks_fts",
    ]:
        assert table_exists(conn, table)
    store.close()
