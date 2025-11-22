import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from .models import (
    FileRecord,
    ChunkRecord,
    SymbolRecord,
    EdgeRecord,
    SummaryRecord,
    ClaimRecord,
    ReportVersionRecord,
    Issue,
)
from .schema import connect, init_db


class Store:
    """
    Thin wrapper around SQLite with Pydantic validation and lifecycle control.
    """

    def __init__(self, db_path: Optional[Path] = None, persist: bool = False, allow_existing: bool = False):
        self.persist = persist
        if db_path is None:
            fd, path_str = tempfile.mkstemp(prefix="tech-writer-", suffix=".db")
            Path(path_str).unlink(missing_ok=True)  # remove temp file; sqlite will recreate
            self.db_path = Path(path_str)
        else:
            self.db_path = Path(db_path)
        if self.db_path.exists() and not allow_existing:
            raise FileExistsError(
                f"Refusing to reuse existing store at {self.db_path}. Pass allow_existing=True to override."
            )
        self.conn = connect(self.db_path)
        init_db(self.conn)

    def close(self):
        self.conn.close()
        if not self.persist:
            try:
                self.db_path.unlink(missing_ok=True)
            except OSError:
                pass

    # --- insert helpers ---
    def add_file(self, record: FileRecord) -> int:
        cur = self.conn.execute(
            "INSERT INTO files(path, hash, lang, size, mtime, parsed) VALUES (?, ?, ?, ?, ?, ?)",
            (record.path, record.hash, record.lang, record.size, record.mtime.isoformat(), int(record.parsed)),
        )
        self.conn.commit()
        return cur.lastrowid

    def add_chunks(self, records: Iterable[ChunkRecord]) -> List[int]:
        ids = []
        for rec in records:
            cur = self.conn.execute(
                "INSERT INTO chunks(file_id, start_line, end_line, kind, text, hash, symbol_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (rec.file_id, rec.start_line, rec.end_line, rec.kind, rec.text, rec.hash, rec.symbol_id),
            )
            ids.append(cur.lastrowid)
        self.conn.commit()
        return ids

    def add_symbols(self, records: Iterable[SymbolRecord]) -> List[int]:
        ids = []
        for rec in records:
            cur = self.conn.execute(
                "INSERT INTO symbols(file_id, name, kind, signature, start_line, end_line, doc, parent_symbol_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    rec.file_id,
                    rec.name,
                    rec.kind,
                    rec.signature,
                    rec.start_line,
                    rec.end_line,
                    rec.doc,
                    rec.parent_symbol_id,
                ),
            )
            ids.append(cur.lastrowid)
        self.conn.commit()
        return ids

    def add_edges(self, records: Iterable[EdgeRecord]) -> None:
        self.conn.executemany(
            "INSERT OR IGNORE INTO edges(src_symbol_id, dst_symbol_id, edge_type) VALUES (?, ?, ?)",
            [(r.src_symbol_id, r.dst_symbol_id, r.edge_type) for r in records],
        )
        self.conn.commit()

    def add_summary(self, record: SummaryRecord) -> int:
        cur = self.conn.execute(
            "INSERT INTO summaries(level, target_id, text, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
            (record.level, record.target_id, record.text, record.confidence, record.created_at.isoformat()),
        )
        self.conn.commit()
        return cur.lastrowid

    def add_report_version(self, record: ReportVersionRecord) -> int:
        cur = self.conn.execute(
            "INSERT INTO report_versions(content, created_at, coverage_score, citation_score, issues_high, issues_med, issues_low) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                record.content,
                record.created_at.isoformat(),
                record.coverage_score,
                record.citation_score,
                record.issues_high,
                record.issues_med,
                record.issues_low,
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def add_claims(self, records: Iterable[ClaimRecord]) -> List[int]:
        ids = []
        for rec in records:
            cur = self.conn.execute(
                "INSERT INTO claims(report_version, text, citation_refs, status, severity, rationale) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    rec.report_version,
                    rec.text,
                    json.dumps(rec.citation_refs),
                    rec.status.value,
                    rec.severity.value,
                    rec.rationale,
                ),
            )
            ids.append(cur.lastrowid)
        self.conn.commit()
        return ids

    def add_chunk_embeddings(self, embeddings: Iterable[tuple[int, bytes, int]]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO chunk_embeddings(chunk_id, vector, dim) VALUES (?, ?, ?)",
            [(cid, vec, dim) for cid, vec, dim in embeddings],
        )
        self.conn.commit()

    def add_symbol_embeddings(self, embeddings: Iterable[tuple[int, bytes, int]]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO symbol_embeddings(symbol_id, vector, dim) VALUES (?, ?, ?)",
            [(sid, vec, dim) for sid, vec, dim in embeddings],
        )
        self.conn.commit()

    def get_chunk_embedding(self, chunk_id: int):
        cur = self.conn.execute(
            "SELECT vector, dim FROM chunk_embeddings WHERE chunk_id = ?", (chunk_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        vec_blob, dim = row
        import numpy as np
        vec = np.frombuffer(vec_blob, dtype=np.float32)
        if vec.shape[0] != dim:
            return None
        return vec

    # --- retrieval helpers ---
    def search_chunks_fts(self, query: str, limit: int = 20) -> List[ChunkRecord]:
        try:
            cur = self.conn.execute(
                """
                SELECT c.id, c.file_id, c.start_line, c.end_line, c.kind, c.text, c.hash, c.symbol_id
                FROM chunks_fts f
                JOIN chunks c ON c.id = f.rowid
                WHERE chunks_fts MATCH ?
                LIMIT ?
                """,
                (query, limit),
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            # Fallback to LIKE search if MATCH fails on special chars
            cur = self.conn.execute(
                """
                SELECT id, file_id, start_line, end_line, kind, text, hash, symbol_id
                FROM chunks
                WHERE text LIKE ?
                LIMIT ?
                """,
                (f"%{query}%", limit),
            )
            rows = cur.fetchall()
        return [
            ChunkRecord(
                id=row[0],
                file_id=row[1],
                start_line=row[2],
                end_line=row[3],
                kind=row[4],
                text=row[5],
                hash=row[6],
                symbol_id=row[7],
            )
            for row in rows
        ]

    def get_file_by_path(self, path: str) -> Optional[FileRecord]:
        cur = self.conn.execute(
            "SELECT id, path, hash, lang, size, mtime, parsed FROM files WHERE path = ?", (path,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return FileRecord(
            id=row[0],
            path=row[1],
            hash=row[2],
            lang=row[3],
            size=row[4],
            mtime=row[5],  # pydantic will parse
            parsed=bool(row[6]),
        )

    def get_file_by_id(self, file_id: int) -> Optional[FileRecord]:
        cur = self.conn.execute(
            "SELECT id, path, hash, lang, size, mtime, parsed FROM files WHERE id = ?", (file_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return FileRecord(
            id=row[0],
            path=row[1],
            hash=row[2],
            lang=row[3],
            size=row[4],
            mtime=row[5],
            parsed=bool(row[6]),
        )

    def get_all_files(self) -> List[FileRecord]:
        cur = self.conn.execute("SELECT id, path, hash, lang, size, mtime, parsed FROM files ORDER BY path")
        rows = cur.fetchall()
        return [
            FileRecord(id=r[0], path=r[1], hash=r[2], lang=r[3], size=r[4], mtime=r[5], parsed=bool(r[6]))
            for r in rows
        ]

    def add_package(self, path: str, name: str) -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO packages(path, name) VALUES (?, ?)",
            (path, name),
        )
        if cur.lastrowid:
            self.conn.commit()
            return cur.lastrowid
        cur = self.conn.execute("SELECT id FROM packages WHERE path=?", (path,))
        row = cur.fetchone()
        return row[0]

    def add_module(self, path: str, name: str, package_id: int | None) -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO modules(path, name, package_id) VALUES (?, ?, ?)",
            (path, name, package_id),
        )
        if cur.lastrowid:
            self.conn.commit()
            return cur.lastrowid
        cur = self.conn.execute("SELECT id FROM modules WHERE path=?", (path,))
        row = cur.fetchone()
        return row[0]

    def link_file_to_module(self, module_id: int, file_id: int) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO module_files(module_id, file_id) VALUES (?, ?)",
            (module_id, file_id),
        )
        self.conn.commit()

    def get_chunks_for_file(self, file_id: int) -> List[ChunkRecord]:
        cur = self.conn.execute(
            "SELECT id, file_id, start_line, end_line, kind, text, hash, symbol_id FROM chunks WHERE file_id = ? ORDER BY start_line",
            (file_id,),
        )
        rows = cur.fetchall()
        return [
            ChunkRecord(
                id=row[0],
                file_id=row[1],
                start_line=row[2],
                end_line=row[3],
                kind=row[4],
                text=row[5],
                hash=row[6],
                symbol_id=row[7],
            )
            for row in rows
        ]

    def get_symbols_for_file(self, file_id: int) -> List[SymbolRecord]:
        cur = self.conn.execute(
            "SELECT id, file_id, name, kind, signature, start_line, end_line, doc, parent_symbol_id FROM symbols WHERE file_id = ?",
            (file_id,),
        )
        rows = cur.fetchall()
        return [
            SymbolRecord(
                id=row[0],
                file_id=row[1],
                name=row[2],
                kind=row[3],
                signature=row[4],
                start_line=row[5],
                end_line=row[6],
                doc=row[7],
                parent_symbol_id=row[8],
            )
            for row in rows
        ]

    def get_edges_for_symbol(self, symbol_id: int) -> List[EdgeRecord]:
        cur = self.conn.execute(
            "SELECT src_symbol_id, dst_symbol_id, edge_type FROM edges WHERE src_symbol_id = ? OR dst_symbol_id = ?",
            (symbol_id, symbol_id),
        )
        rows = cur.fetchall()
        return [EdgeRecord(src_symbol_id=r[0], dst_symbol_id=r[1], edge_type=r[2]) for r in rows]

    def find_chunk_covering_range(self, file_id: int, start: int, end: int) -> Optional[ChunkRecord]:
        cur = self.conn.execute(
            """
            SELECT id, file_id, start_line, end_line, kind, text, hash, symbol_id
            FROM chunks
            WHERE file_id = ?
              AND start_line <= ?
              AND end_line >= ?
            LIMIT 1
            """,
            (file_id, start, end),
        )
        row = cur.fetchone()
        if not row:
            return None
        return ChunkRecord(
            id=row[0],
            file_id=row[1],
            start_line=row[2],
            end_line=row[3],
            kind=row[4],
            text=row[5],
            hash=row[6],
            symbol_id=row[7],
        )

    # --- audit logging helpers ---
    def log_retrieval_event(
        self,
        report_version: int,
        iteration: int,
        prompt: str,
        chunks: List[ChunkRecord],
        summaries: List[SummaryRecord],
        symbols: List[SymbolRecord],
        edges: List[EdgeRecord],
    ) -> int:
        payload_chunks = [
            {"id": c.id, "file_id": c.file_id, "start": c.start_line, "end": c.end_line, "kind": c.kind} for c in chunks
        ]
        payload_summaries = [{"id": s.id, "level": s.level, "target_id": s.target_id} for s in summaries]
        payload_symbols = [{"id": s.id, "file_id": s.file_id, "name": s.name, "kind": s.kind} for s in symbols]
        payload_edges = [{"src": e.src_symbol_id, "dst": e.dst_symbol_id, "type": e.edge_type} for e in edges]
        cur = self.conn.execute(
            """
            INSERT INTO retrieval_events(report_version, iteration, prompt, chunks, summaries, symbols, edges, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_version,
                iteration,
                prompt,
                json.dumps(payload_chunks),
                json.dumps(payload_summaries),
                json.dumps(payload_symbols),
                json.dumps(payload_edges),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def log_iteration_status(
        self,
        report_version: int,
        iteration: int,
        coverage: float,
        support_rate: float,
        citation_rate: float,
        issues_high: int,
        issues_med: int,
        issues_low: int,
        missing_citations: int,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO iteration_status(
                report_version, iteration, coverage, support_rate, citation_rate,
                issues_high, issues_med, issues_low, missing_citations, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_version,
                iteration,
                coverage,
                support_rate,
                citation_rate,
                issues_high,
                issues_med,
                issues_low,
                missing_citations,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def log_iteration_issues(self, report_version: int, iteration: int, issues: List[Issue]) -> None:
        rows = [
            (
                report_version,
                iteration,
                issue.severity.value,
                issue.description,
                issue.fix_hint,
                datetime.now(timezone.utc).isoformat(),
            )
            for issue in issues
        ]
        if not rows:
            return
        self.conn.executemany(
            """
            INSERT INTO iteration_issues(report_version, iteration, severity, description, fix_hint, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()
