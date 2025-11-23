"""
SQLite-based cache store for file content and metadata.

Provides persistent storage for:
- File content with language detection
- Full-text search via FTS5
- Parsed symbols and imports
"""

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class CachedFile:
    """A file stored in the cache."""
    id: int
    path: str
    content: str
    language: str
    line_count: int
    hash: str
    cached_at: str


@dataclass
class Symbol:
    """A symbol (function, class, etc.) from a file."""
    name: str
    kind: str
    line: int
    end_line: Optional[int] = None
    signature: Optional[str] = None
    doc: Optional[str] = None
    file_id: Optional[int] = None
    file_path: Optional[str] = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    lang TEXT,
    line_count INTEGER NOT NULL,
    hash TEXT NOT NULL,
    cached_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id),
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    line INTEGER NOT NULL,
    end_line INTEGER,
    signature TEXT,
    doc TEXT
);

CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);
CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
"""

FTS_SCHEMA = """
-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
    path,
    content,
    content='files',
    content_rowid='id'
);

-- Triggers to keep FTS index in sync with files table
CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
    INSERT INTO files_fts(rowid, path, content) VALUES (new.id, new.path, new.content);
END;

CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, path, content) VALUES('delete', old.id, old.path, old.content);
END;

CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, path, content) VALUES('delete', old.id, old.path, old.content);
    INSERT INTO files_fts(rowid, path, content) VALUES (new.id, new.path, new.content);
END;
"""


class CacheStore:
    """SQLite cache for file content and metadata."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the cache store.

        Args:
            db_path: Path to SQLite database. If None, uses in-memory DB.
        """
        self.db_path = db_path or ":memory:"
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema including FTS."""
        self._conn.executescript(SCHEMA)
        self._conn.executescript(FTS_SCHEMA)
        self._conn.commit()

    def _hash_content(self, content: str) -> str:
        """Generate hash of file content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def add_file(self, path: str, content: str, language: str) -> int:
        """
        Add a file to the cache.

        If file already exists, updates content and returns same ID.

        Args:
            path: File path (relative to repo root)
            content: File content
            language: Programming language

        Returns:
            File ID
        """
        line_count = content.count('\n') + 1 if content else 0
        content_hash = self._hash_content(content)
        cached_at = datetime.utcnow().isoformat()

        cursor = self._conn.execute(
            "SELECT id FROM files WHERE path = ?",
            (path,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing file
            self._conn.execute(
                """UPDATE files
                   SET content = ?, lang = ?, line_count = ?, hash = ?, cached_at = ?
                   WHERE id = ?""",
                (content, language, line_count, content_hash, cached_at, existing['id'])
            )
            self._conn.commit()
            return existing['id']
        else:
            # Insert new file
            cursor = self._conn.execute(
                """INSERT INTO files (path, content, lang, line_count, hash, cached_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (path, content, language, line_count, content_hash, cached_at)
            )
            self._conn.commit()
            return cursor.lastrowid

    def get_file(self, path: str) -> Optional[CachedFile]:
        """Retrieve a file from the cache by path."""
        cursor = self._conn.execute(
            "SELECT * FROM files WHERE path = ?",
            (path,)
        )
        row = cursor.fetchone()
        if row:
            return CachedFile(
                id=row['id'],
                path=row['path'],
                content=row['content'],
                language=row['lang'],
                line_count=row['line_count'],
                hash=row['hash'],
                cached_at=row['cached_at']
            )
        return None

    def get_file_by_id(self, file_id: int) -> Optional[CachedFile]:
        """Retrieve a file from the cache by ID."""
        cursor = self._conn.execute(
            "SELECT * FROM files WHERE id = ?",
            (file_id,)
        )
        row = cursor.fetchone()
        if row:
            return CachedFile(
                id=row['id'],
                path=row['path'],
                content=row['content'],
                language=row['lang'],
                line_count=row['line_count'],
                hash=row['hash'],
                cached_at=row['cached_at']
            )
        return None

    def has_file(self, path: str) -> bool:
        """Check if a file is cached."""
        cursor = self._conn.execute(
            "SELECT 1 FROM files WHERE path = ?",
            (path,)
        )
        return cursor.fetchone() is not None

    def add_symbols(self, file_id: int, symbols: list[Symbol]) -> None:
        """
        Add symbols for a file.

        Clears existing symbols for the file first.

        Args:
            file_id: File ID
            symbols: List of symbols to add
        """
        # Clear existing symbols for this file
        self._conn.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))

        # Insert new symbols
        for sym in symbols:
            self._conn.execute(
                """INSERT INTO symbols (file_id, name, kind, line, end_line, signature, doc)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (file_id, sym.name, sym.kind, sym.line, sym.end_line, sym.signature, sym.doc)
            )
        self._conn.commit()

    def get_symbols(self, file_id: int) -> list[Symbol]:
        """Get all symbols for a file."""
        cursor = self._conn.execute(
            """SELECT s.*, f.path as file_path
               FROM symbols s JOIN files f ON s.file_id = f.id
               WHERE file_id = ?""",
            (file_id,)
        )
        return [
            Symbol(
                name=row['name'],
                kind=row['kind'],
                line=row['line'],
                end_line=row['end_line'],
                signature=row['signature'],
                doc=row['doc'],
                file_id=row['file_id'],
                file_path=row['file_path']
            )
            for row in cursor.fetchall()
        ]

    def get_all_symbols(self) -> list[Symbol]:
        """Get all symbols across all files."""
        cursor = self._conn.execute(
            """SELECT s.*, f.path as file_path
               FROM symbols s JOIN files f ON s.file_id = f.id"""
        )
        return [
            Symbol(
                name=row['name'],
                kind=row['kind'],
                line=row['line'],
                end_line=row['end_line'],
                signature=row['signature'],
                doc=row['doc'],
                file_id=row['file_id'],
                file_path=row['file_path']
            )
            for row in cursor.fetchall()
        ]

    def get_symbols_by_name(self, name: str) -> list[Symbol]:
        """Find symbols by name across all files."""
        cursor = self._conn.execute(
            """SELECT s.*, f.path as file_path
               FROM symbols s JOIN files f ON s.file_id = f.id
               WHERE s.name = ?""",
            (name,)
        )
        return [
            Symbol(
                name=row['name'],
                kind=row['kind'],
                line=row['line'],
                end_line=row['end_line'],
                signature=row['signature'],
                doc=row['doc'],
                file_id=row['file_id'],
                file_path=row['file_path']
            )
            for row in cursor.fetchall()
        ]

    def list_cached_files(self) -> list[str]:
        """List all cached file paths."""
        cursor = self._conn.execute("SELECT path FROM files ORDER BY path")
        return [row['path'] for row in cursor.fetchall()]

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """
        Full-text search across cached files using FTS5.

        Args:
            query: Search string (will be escaped for literal search)
            limit: Maximum results to return

        Returns:
            List of matches: [{"path": str, "line": int, "snippet": str, "score": float}, ...]
        """
        if not query or not query.strip():
            return []

        # Escape special FTS5 characters for literal search
        escaped_query = self._escape_fts_query(query)

        try:
            cursor = self._conn.execute(
                """
                SELECT
                    f.path,
                    f.content,
                    bm25(files_fts) as score
                FROM files_fts
                JOIN files f ON files_fts.rowid = f.id
                WHERE files_fts MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (escaped_query, limit * 2)  # Fetch extra to account for line-level filtering
            )

            results = []
            query_lower = query.lower()

            for row in cursor.fetchall():
                path = row["path"]
                content = row["content"]
                score = row["score"]

                # Find matching lines within the file
                for line_num, line in enumerate(content.splitlines(), start=1):
                    if query_lower in line.lower():
                        results.append({
                            "path": path,
                            "line": line_num,
                            "snippet": line.strip(),
                            "score": score,
                        })
                        if len(results) >= limit:
                            return results

            return results

        except sqlite3.OperationalError:
            # FTS query failed, fall back to simple search
            return self._simple_search(query, limit)

    def _escape_fts_query(self, query: str) -> str:
        """Escape special FTS5 characters for literal search."""
        # FTS5 special chars: AND OR NOT ( ) " *
        # Wrap in quotes for phrase search
        escaped = query.replace('"', '""')
        return f'"{escaped}"'

    def _simple_search(self, query: str, limit: int) -> list[dict]:
        """Fallback simple search when FTS fails."""
        results = []
        query_lower = query.lower()

        cursor = self._conn.execute("SELECT path, content FROM files")
        for row in cursor.fetchall():
            path = row["path"]
            content = row["content"]

            for line_num, line in enumerate(content.splitlines(), start=1):
                if query_lower in line.lower():
                    results.append({
                        "path": path,
                        "line": line_num,
                        "snippet": line.strip(),
                        "score": 0.0,
                    })
                    if len(results) >= limit:
                        return results

        return results

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
