import argparse
from pathlib import Path

from .store import Store


def parse_args():
    parser = argparse.ArgumentParser(description="Audit a persisted store.")
    parser.add_argument("store", help="Path to SQLite store (persisted).")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-files")
    sub.add_parser("list-reports")
    show_report = sub.add_parser("show-report")
    show_report.add_argument("--id", type=int, required=True)
    list_claims = sub.add_parser("list-claims")
    list_claims.add_argument("--report-id", type=int, required=True)
    list_symbols = sub.add_parser("list-symbols")
    list_symbols.add_argument("--file-id", type=int, required=False)
    search_chunks = sub.add_parser("search-chunks")
    search_chunks.add_argument("--query", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    store = Store(db_path=Path(args.store), persist=True)
    try:
        if args.command == "list-files":
            for f in store.get_all_files():
                print(f"{f.id}\t{f.path}\t{f.lang}")
        elif args.command == "list-reports":
            cur = store.conn.execute("SELECT id, created_at, coverage_score, citation_score FROM report_versions")
            for row in cur.fetchall():
                print(f"id={row[0]} created={row[1]} coverage={row[2]:.2f} citations={row[3]:.2f}")
        elif args.command == "show-report":
            cur = store.conn.execute("SELECT content FROM report_versions WHERE id=?", (args.id,))
            row = cur.fetchone()
            if not row:
                print("Not found")
            else:
                print(row[0])
        elif args.command == "list-claims":
            cur = store.conn.execute(
                "SELECT id, text, status, severity FROM claims WHERE report_version=?", (args.report_id,)
            )
            for row in cur.fetchall():
                print(f"id={row[0]} status={row[2]} severity={row[3]} text={row[1]}")
        elif args.command == "list-symbols":
            if args.file_id:
                syms = store.get_symbols_for_file(args.file_id)
            else:
                cur = store.conn.execute("SELECT id FROM files")
                syms = []
                for row in cur.fetchall():
                    syms.extend(store.get_symbols_for_file(row[0]))
            for s in syms:
                print(f"id={s.id} file={s.file_id} kind={s.kind} name={s.name} [{s.start_line}-{s.end_line}]")
        elif args.command == "search-chunks":
            chunks = store.search_chunks_fts(args.query, limit=20)
            for c in chunks:
                print(f"id={c.id} file={c.file_id} [{c.start_line}-{c.end_line}] {c.text[:80]}")
    finally:
        store.close()


if __name__ == "__main__":
    main()
