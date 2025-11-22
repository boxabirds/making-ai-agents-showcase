import argparse
from pathlib import Path
from dotenv import load_dotenv

from infinite_scalability.ingest import ingest_repo
from infinite_scalability.store import Store


def main():
    load_dotenv(".env.test")
    parser = argparse.ArgumentParser(description="Task 2 manual check: ingest with tree-sitter.")
    parser.add_argument("directory", help="Directory to ingest")
    parser.add_argument("--persist", action="store_true", help="Keep DB after run")
    parser.add_argument("--db-path", default=None, help="Optional path for DB")
    parser.add_argument("--ingest-file-limit", default=None, help="Optional file limit")
    args = parser.parse_args()

    if args.ingest_file_limit:
        import os
        os.environ["INGEST_FILE_LIMIT"] = args.ingest_file_limit

    db_path = Path(args.db_path) if args.db_path else None
    store = Store(db_path=db_path, persist=args.persist)
    try:
        ingest_repo(Path(args.directory), store)
        cur = store.conn.execute("SELECT COUNT(*) FROM files")
        files = cur.fetchone()[0]
        cur = store.conn.execute("SELECT COUNT(*) FROM chunks")
        chunks = cur.fetchone()[0]
        cur = store.conn.execute("SELECT COUNT(*) FROM symbols")
        symbols = cur.fetchone()[0]
        print(f"Ingest complete: files={files}, chunks={chunks}, symbols={symbols}")
    finally:
        store.close()


if __name__ == "__main__":
    main()
