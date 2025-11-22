from typing import List, Tuple, Dict

import numpy as np
from .models import ChunkRecord, RetrievedContext, SummaryRecord, SymbolRecord, EdgeRecord
from .store import Store
import sqlite3


def retrieve_chunks(store: Store, query: str, limit: int = 20) -> List[ChunkRecord]:
    """
    Deterministic-first retrieval over FTS for chunks.
    """
    return store.search_chunks_fts(query, limit=limit)


def retrieve_summaries(store: Store, query: str, limit: int = 10) -> List[SummaryRecord]:
    """
    Summary retrieval via FTS over summaries text with lexical filter fallback.
    """
    try:
        cur = store.conn.execute(
            """
            SELECT s.id, s.level, s.target_id, s.text, s.confidence, s.created_at
            FROM summaries_fts f
            JOIN summaries s ON s.id = f.rowid
            WHERE summaries_fts MATCH ?
            LIMIT ?
            """,
            (query, limit),
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        cur = store.conn.execute(
            "SELECT id, level, target_id, text, confidence, created_at FROM summaries WHERE text LIKE ? ORDER BY confidence DESC LIMIT ?",
            (f"%{query}%", limit),
        )
        rows = cur.fetchall()
    return [
        SummaryRecord(
            id=r[0],
            level=r[1],
            target_id=r[2],
            text=r[3],
            confidence=r[4],
            created_at=r[5],
        )
        for r in rows
    ]


def retrieve_symbols(store: Store, query: str, limit: int = 20) -> List[SymbolRecord]:
    cur = store.conn.execute(
        "SELECT id, file_id, name, kind, signature, start_line, end_line, doc, parent_symbol_id FROM symbols WHERE name LIKE ? LIMIT ?",
        (f"%{query}%", limit),
    )
    rows = cur.fetchall()
    return [
        SymbolRecord(
            id=r[0],
            file_id=r[1],
            name=r[2],
            kind=r[3],
            signature=r[4],
            start_line=r[5],
            end_line=r[6],
            doc=r[7],
            parent_symbol_id=r[8],
        )
        for r in rows
    ]


def retrieve_edges(store: Store, symbols: List[SymbolRecord], limit: int = 50) -> List[EdgeRecord]:
    edges: List[EdgeRecord] = []
    for sym in symbols[:limit]:
        edges.extend(store.get_edges_for_symbol(sym.id))  # type: ignore
    return edges


def retrieve_embeddings(store: Store, query_vec: np.ndarray, limit: int = 20) -> List[ChunkRecord]:
    """
    Placeholder: if embeddings were stored, a cosine similarity search would run here.
    Currently returns empty until embeddings are populated.
    """
    try:
        cur = store.conn.execute("SELECT chunk_id, vector, dim FROM chunk_embeddings")
    except sqlite3.OperationalError:
        return []
    rows = cur.fetchall()
    scored: List[tuple[float, int]] = []
    for chunk_id, vec_blob, dim in rows:
        vec = np.frombuffer(vec_blob, dtype=np.float32)
        if vec.shape[0] != dim:
            continue
        if np.linalg.norm(vec) == 0 or np.linalg.norm(query_vec) == 0:
            continue
        score = float(np.dot(vec, query_vec) / (np.linalg.norm(vec) * np.linalg.norm(query_vec)))
        scored.append((score, chunk_id))
    scored.sort(reverse=True)
    chunk_ids = [cid for _, cid in scored[:limit]]
    if not chunk_ids:
        return []
    placeholders = ",".join(["?"] * len(chunk_ids))
    cur = store.conn.execute(
        f"SELECT id, file_id, start_line, end_line, kind, text, hash FROM chunks WHERE id IN ({placeholders})",
        chunk_ids,
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
        )
        for row in rows
    ]


def retrieve_context(store: Store, topic: str, limit: int = 20, query_vec: np.ndarray | None = None) -> RetrievedContext:
    """
    Minimal context retrieval placeholder. Expands topic to chunks, summaries, symbols, edges.
    """
    scored: Dict[int, float] = {}
    # base: FTS chunks
    chunks = retrieve_chunks(store, topic, limit=limit)
    for c in chunks:
        if c.id is not None:
            scored[c.id] = scored.get(c.id, 0.0) + 1.0
    if query_vec is not None:
        emb_chunks = retrieve_embeddings(store, query_vec, limit=max(5, limit // 2))
        for c in emb_chunks:
            if c.id is not None:
                scored[c.id] = scored.get(c.id, 0.0) + 0.2  # embeddings helper-only
        chunks.extend(emb_chunks)
    summaries = retrieve_summaries(store, topic, limit=max(5, limit // 2))
    for s in summaries:
        # boost chunks from summary target if available
        related_file = None
        if s.level == "file":
            related_file = store.get_file_by_id(s.target_id)
        if related_file:
            file_chunks = store.get_chunks_for_file(related_file.id)  # type: ignore
            if file_chunks:
                top_chunk = file_chunks[0]
                chunks.append(top_chunk)
                if top_chunk.id is not None:
                    scored[top_chunk.id] = scored.get(top_chunk.id, 0.0) + 0.5
    symbols = retrieve_symbols(store, topic, limit=max(5, limit // 2))
    edges = retrieve_edges(store, symbols)
    # Pull chunks from symbol files to improve recall
    symbol_related_chunks: List[ChunkRecord] = []
    for sym in symbols:
        sym_chunks = store.get_chunks_for_file(sym.file_id)
        if sym_chunks:
            symbol_related_chunks.append(sym_chunks[0])
            if sym_chunks[0].id is not None:
                scored[sym_chunks[0].id] = scored.get(sym_chunks[0].id, 0.0) + 0.3
    chunks.extend(symbol_related_chunks)
    # expand via edges
    for edge in edges:
        for sym_id in (edge.src_symbol_id, edge.dst_symbol_id):
            sym = next((s for s in symbols if s.id == sym_id), None)
            if sym:
                file_chunks = store.get_chunks_for_file(sym.file_id)
                if file_chunks:
                    chunks.append(file_chunks[0])
                    if file_chunks[0].id is not None:
                        scored[file_chunks[0].id] = scored.get(file_chunks[0].id, 0.0) + 0.2
    # simple re-rank: prioritize chunks that overlap topic tokens
    def score_chunk(c: ChunkRecord) -> int:
        return sum(1 for tok in topic.lower().split() if tok in c.text.lower())
    deduped = []
    seen = set()
    for c in chunks:
        if c.id is None or c.id in seen:
            continue
        seen.add(c.id)
        total_score = scored.get(c.id, 0.0) + score_chunk(c)
        deduped.append((total_score, c))
    deduped.sort(key=lambda x: x[0], reverse=True)
    chunks = [c for _, c in deduped[:limit]]
    return RetrievedContext(chunks=chunks, summaries=summaries, symbols=symbols, edges=edges)
