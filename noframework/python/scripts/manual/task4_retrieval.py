import argparse
from pathlib import Path
from dotenv import load_dotenv
import numpy as np

from infinite_scalability.ingest import ingest_repo
from infinite_scalability.retrieval import retrieve_context
from infinite_scalability.store import Store


def main():
    load_dotenv(".env.test")
    parser = argparse.ArgumentParser(description="Task 4 manual check: hybrid retrieval.")
    parser.add_argument("directory", help="Directory to ingest and query")
    parser.add_argument("--query", default="main", help="Query/topic")
    parser.add_argument("--persist", action="store_true", help="Keep DB after run")
    parser.add_argument("--db-path", default=None, help="Optional path for DB")
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else None
    store = Store(db_path=db_path, persist=args.persist)
    try:
        ingest_repo(Path(args.directory), store)
        # optional: use first chunk embedding as query vector
        query_vec = None
        first_file = store.get_all_files()[0]
        first_chunk = store.get_chunks_for_file(first_file.id)[0]  # type: ignore
        emb = store.get_chunk_embedding(first_chunk.id)  # type: ignore
        if emb is not None:
            query_vec = emb
        ctx = retrieve_context(store, args.query, query_vec=query_vec)
        print(f"Retrieved {len(ctx.chunks)} chunks, {len(ctx.summaries)} summaries, {len(ctx.symbols)} symbols.")
        for c in ctx.chunks[:5]:
            print(f"- {c.kind} [{c.start_line}-{c.end_line}] {c.text[:80]}")
    finally:
        store.close()


if __name__ == "__main__":
    main()
