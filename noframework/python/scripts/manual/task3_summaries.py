import argparse
from pathlib import Path
from dotenv import load_dotenv

from infinite_scalability.ingest import ingest_repo
from infinite_scalability.summarize import summarize_file, summarize_module
from infinite_scalability.validation import validate_summary
from infinite_scalability.store import Store


def main():
    load_dotenv(".env.test")
    parser = argparse.ArgumentParser(description="Task 3 manual check: summaries map/reduce + validation.")
    parser.add_argument("directory", help="Directory to summarize")
    parser.add_argument("--persist", action="store_true", help="Keep DB after run")
    parser.add_argument("--db-path", default=None, help="Optional path for DB")
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else None
    store = Store(db_path=db_path, persist=args.persist)
    try:
        ingest_repo(Path(args.directory), store)
        file_recs = store.get_all_files()
        file_summaries = []
        for f in file_recs:
            s = summarize_file(store, f.id)  # type: ignore
            validate_summary(store, s)
            file_summaries.append(s)
        module_summary = summarize_module(store, args.directory, file_summaries)
        validate_summary(store, module_summary)
        print("Summaries validated successfully.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
