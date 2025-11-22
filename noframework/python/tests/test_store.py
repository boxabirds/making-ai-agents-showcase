import sqlite3
from pathlib import Path

import pytest

from infinite_scalability.store import Store
from infinite_scalability.schema import init_db
from infinite_scalability.models import SummaryRecord
from datetime import datetime, timezone


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
        "retrieval_events",
        "iteration_status",
        "iteration_issues",
    ]:
        assert table_exists(conn, table)
    store.close()


def test_store_rejects_reuse(tmp_path: Path):
    db_path = tmp_path / "reuse.db"
    store = Store(db_path=db_path, persist=True, allow_existing=True)
    store.close()
    with pytest.raises(FileExistsError):
        Store(db_path=db_path, persist=True)


def test_summary_target_fk(tmp_path: Path):
    store = Store(persist=False)
    bad_summary = SummaryRecord(
        level="file",
        target_id=9999,
        text="invalid [file:1-1]",
        confidence=0.5,
        created_at=datetime.now(timezone.utc),
    )
    with pytest.raises(sqlite3.IntegrityError):
        store.add_summary(bad_summary)
    store.close()
