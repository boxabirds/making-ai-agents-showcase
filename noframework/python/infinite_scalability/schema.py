import sqlite3
from pathlib import Path
from typing import Optional


PRAGMAS = [
    ("foreign_keys", "ON"),
    ("journal_mode", "WAL"),
    ("synchronous", "NORMAL"),
    ("temp_store", "MEMORY"),
]


def apply_pragmas(conn: sqlite3.Connection) -> None:
    for pragma, value in PRAGMAS:
        conn.execute(f"PRAGMA {pragma}={value};")


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA defer_foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            hash TEXT NOT NULL,
            lang TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime TEXT NOT NULL,
            parsed INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            kind TEXT NOT NULL,
            text TEXT NOT NULL,
            hash TEXT NOT NULL,
            symbol_id INTEGER,
            FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE,
            FOREIGN KEY(symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS symbols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            signature TEXT,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            doc TEXT,
            parent_symbol_id INTEGER,
            FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE,
            FOREIGN KEY(parent_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            package_id INTEGER,
            FOREIGN KEY(package_id) REFERENCES packages(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS module_files (
            module_id INTEGER NOT NULL,
            file_id INTEGER NOT NULL,
            PRIMARY KEY(module_id, file_id),
            FOREIGN KEY(module_id) REFERENCES modules(id) ON DELETE CASCADE,
            FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS edges (
            src_symbol_id INTEGER NOT NULL,
            dst_symbol_id INTEGER NOT NULL,
            edge_type TEXT NOT NULL,
            FOREIGN KEY(src_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,
            FOREIGN KEY(dst_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            confidence REAL NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS report_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            coverage_score REAL NOT NULL,
            citation_score REAL NOT NULL,
            issues_high INTEGER NOT NULL,
            issues_med INTEGER NOT NULL,
            issues_low INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_version INTEGER NOT NULL,
            text TEXT NOT NULL,
            citation_refs TEXT NOT NULL,
            status TEXT NOT NULL,
            severity TEXT NOT NULL,
            rationale TEXT NOT NULL,
            FOREIGN KEY(report_version) REFERENCES report_versions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chunk_embeddings (
            chunk_id INTEGER PRIMARY KEY,
            vector BLOB NOT NULL,
            dim INTEGER NOT NULL,
            FOREIGN KEY(chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS symbol_embeddings (
            symbol_id INTEGER PRIMARY KEY,
            vector BLOB NOT NULL,
            dim INTEGER NOT NULL,
            FOREIGN KEY(symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            text,
            content='chunks',
            content_rowid='id'
        );

        CREATE TABLE IF NOT EXISTS retrieval_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_version INTEGER NOT NULL,
            iteration INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            chunks TEXT NOT NULL,
            summaries TEXT NOT NULL,
            symbols TEXT NOT NULL,
            edges TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(report_version) REFERENCES report_versions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS iteration_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_version INTEGER NOT NULL,
            iteration INTEGER NOT NULL,
            coverage REAL NOT NULL,
            support_rate REAL NOT NULL,
            citation_rate REAL NOT NULL,
            issues_high INTEGER NOT NULL,
            issues_med INTEGER NOT NULL,
            issues_low INTEGER NOT NULL,
            missing_citations INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(report_version) REFERENCES report_versions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS iteration_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_version INTEGER NOT NULL,
            iteration INTEGER NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            fix_hint TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(report_version) REFERENCES report_versions(id) ON DELETE CASCADE
        );

        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES('delete', old.id, old.text);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES('delete', old.id, old.text);
            INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text);
        END;

        CREATE VIRTUAL TABLE IF NOT EXISTS summaries_fts USING fts5(
            text,
            content='summaries',
            content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS summaries_ai AFTER INSERT ON summaries BEGIN
            INSERT INTO summaries_fts(rowid, text) VALUES (new.id, new.text);
        END;
        CREATE TRIGGER IF NOT EXISTS summaries_ad AFTER DELETE ON summaries BEGIN
            INSERT INTO summaries_fts(summaries_fts, rowid, text) VALUES('delete', old.id, old.text);
        END;
        CREATE TRIGGER IF NOT EXISTS summaries_au AFTER UPDATE ON summaries BEGIN
            INSERT INTO summaries_fts(summaries_fts, rowid, text) VALUES('delete', old.id, old.text);
            INSERT INTO summaries_fts(rowid, text) VALUES (new.id, new.text);
        END;

        CREATE TRIGGER IF NOT EXISTS summaries_file_target_check
        BEFORE INSERT ON summaries
        WHEN new.level = 'file' AND NOT EXISTS (SELECT 1 FROM files WHERE id = new.target_id)
        BEGIN
            SELECT RAISE(ABORT, 'invalid file summary target');
        END;

        CREATE TRIGGER IF NOT EXISTS summaries_module_target_check
        BEFORE INSERT ON summaries
        WHEN new.level = 'module' AND NOT EXISTS (SELECT 1 FROM modules WHERE id = new.target_id)
        BEGIN
            SELECT RAISE(ABORT, 'invalid module summary target');
        END;

        CREATE TRIGGER IF NOT EXISTS summaries_package_target_check
        BEFORE INSERT ON summaries
        WHEN new.level = 'package' AND NOT EXISTS (SELECT 1 FROM packages WHERE id = new.target_id)
        BEGIN
            SELECT RAISE(ABORT, 'invalid package summary target');
        END;

        CREATE TRIGGER IF NOT EXISTS summaries_chunk_target_check
        BEFORE INSERT ON summaries
        WHEN new.level = 'chunk' AND NOT EXISTS (SELECT 1 FROM chunks WHERE id = new.target_id)
        BEGIN
            SELECT RAISE(ABORT, 'invalid chunk summary target');
        END;

        CREATE INDEX IF NOT EXISTS idx_symbols_name_kind ON symbols(name, kind);
        CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_symbol ON chunks(symbol_id);
        CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_symbol_id);
        CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_symbol_id);
        CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_unique ON edges(src_symbol_id, dst_symbol_id, edge_type);
        CREATE INDEX IF NOT EXISTS idx_summaries_target_level ON summaries(target_id, level);
        CREATE INDEX IF NOT EXISTS idx_claims_report_version ON claims(report_version);
        CREATE INDEX IF NOT EXISTS idx_modules_path ON modules(path);
        CREATE INDEX IF NOT EXISTS idx_packages_path ON packages(path);
        CREATE INDEX IF NOT EXISTS idx_module_files_file ON module_files(file_id);
        CREATE INDEX IF NOT EXISTS idx_iteration_status_rv_iter ON iteration_status(report_version, iteration);
        CREATE INDEX IF NOT EXISTS idx_iteration_issues_rv_iter ON iteration_issues(report_version, iteration);
        CREATE INDEX IF NOT EXISTS idx_retrieval_events_rv_iter ON retrieval_events(report_version, iteration);
        """
    )
    conn.commit()


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    apply_pragmas(conn)
    return conn


class StoreManager:
    """
    Context manager for SQLite lifecycle. Deletes DB on exit when persist=False.
    """

    def __init__(self, db_path: Path, persist: bool = False, allow_existing: bool = False):
        self.db_path = Path(db_path)
        self.persist = persist
        self.allow_existing = allow_existing
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        if self.db_path.exists() and not self.allow_existing:
            raise FileExistsError(
                f"Refusing to reuse existing store at {self.db_path}. Pass allow_existing=True to override."
            )
        self.conn = connect(self.db_path)
        init_db(self.conn)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
        if not self.persist:
            try:
                self.db_path.unlink(missing_ok=True)
            except OSError:
                pass
        # do not suppress exceptions
        return False
