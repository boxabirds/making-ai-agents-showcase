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
    export_report = sub.add_parser("export-report")
    export_report.add_argument("--id", type=int, required=True)
    export_report.add_argument("--out", type=Path, required=True)
    list_claims = sub.add_parser("list-claims")
    list_claims.add_argument("--report-id", type=int, required=True)
    list_symbols = sub.add_parser("list-symbols")
    list_symbols.add_argument("--file-id", type=int, required=False)
    list_summaries = sub.add_parser("list-summaries")
    list_summaries.add_argument("--level", choices=["file", "module", "package"], required=False)
    search_chunks = sub.add_parser("search-chunks")
    search_chunks.add_argument("--query", required=True)
    symbol_neighbors = sub.add_parser("symbol-neighbors")
    symbol_neighbors.add_argument("--symbol-id", type=int, required=True)
    symbol_neighbors.add_argument("--edge-type", required=False)
    list_retrievals = sub.add_parser("list-retrieval-events")
    list_retrievals.add_argument("--report-id", type=int, required=False)
    list_iterations = sub.add_parser("list-iteration-status")
    list_iterations.add_argument("--report-id", type=int, required=False)
    list_iteration_issues = sub.add_parser("list-iteration-issues")
    list_iteration_issues.add_argument("--report-id", type=int, required=False)
    return parser.parse_args()


def main():
    args = parse_args()
    store = Store(db_path=Path(args.store), persist=True, allow_existing=True)
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
        elif args.command == "export-report":
            cur = store.conn.execute("SELECT content FROM report_versions WHERE id=?", (args.id,))
            row = cur.fetchone()
            if not row:
                print("Not found")
            else:
                args.out.write_text(row[0])
                print(f"Wrote report {args.id} to {args.out}")
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
        elif args.command == "list-summaries":
            if args.level:
                cur = store.conn.execute(
                    "SELECT id, level, target_id, text, confidence FROM summaries WHERE level=?", (args.level,)
                )
            else:
                cur = store.conn.execute("SELECT id, level, target_id, text, confidence FROM summaries")
            for row in cur.fetchall():
                print(f"id={row[0]} level={row[1]} target={row[2]} conf={row[4]:.2f} text={row[3][:80]}")
        elif args.command == "search-chunks":
            chunks = store.search_chunks_fts(args.query, limit=20)
            for c in chunks:
                print(f"id={c.id} file={c.file_id} [{c.start_line}-{c.end_line}] {c.text[:80]}")
        elif args.command == "symbol-neighbors":
            edges = store.get_edges_for_symbol(args.symbol_id)
            for e in edges:
                if args.edge_type and e.edge_type != args.edge_type:
                    continue
                print(f"{e.src_symbol_id} -[{e.edge_type}]-> {e.dst_symbol_id}")
        elif args.command == "list-retrieval-events":
            cur = store.conn.execute(
                "SELECT id, report_version, iteration, created_at FROM retrieval_events WHERE (? IS NULL OR report_version=?) ORDER BY report_version, iteration",
                (args.report_id, args.report_id),
            )
            for row in cur.fetchall():
                print(f"id={row[0]} report={row[1]} iter={row[2]} created={row[3]}")
        elif args.command == "list-iteration-status":
            cur = store.conn.execute(
                """
                SELECT id, report_version, iteration, coverage, support_rate, citation_rate, issues_high, issues_med, issues_low, missing_citations, created_at
                FROM iteration_status
                WHERE (? IS NULL OR report_version=?)
                ORDER BY report_version, iteration
                """,
                (args.report_id, args.report_id),
            )
            for row in cur.fetchall():
                print(
                    f"id={row[0]} report={row[1]} iter={row[2]} "
                    f"cov={row[3]:.2f} support={row[4]:.2f} cite={row[5]:.2f} "
                    f"issues(high/med/low)={row[6]}/{row[7]}/{row[8]} missing_citations={row[9]} created={row[10]}"
                )
        elif args.command == "list-iteration-issues":
            cur = store.conn.execute(
                """
                SELECT id, report_version, iteration, severity, description, fix_hint, created_at
                FROM iteration_issues
                WHERE (? IS NULL OR report_version=?)
                ORDER BY report_version, iteration, id
                """,
                (args.report_id, args.report_id),
            )
            for row in cur.fetchall():
                hint = f" hint={row[5]}" if row[5] else ""
                print(
                    f"id={row[0]} report={row[1]} iter={row[2]} severity={row[3]} desc={row[4]}{hint} created={row[6]}"
                )
    finally:
        store.close()


if __name__ == "__main__":
    main()
