import argparse
import json
from pathlib import Path

from common.utils import configure_code_base_source, read_prompt_file

from .orchestrator import run_pipeline
from .store import Store
from .eval import evaluate_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run evaluation for a repo/prompt and emit metrics.")
    parser.add_argument("--prompt", required=True, help="Path to prompt file.")
    parser.add_argument("--repo", help="GitHub repo URL (e.g., https://github.com/axios/axios)")
    parser.add_argument("directory", nargs="?", help="Local directory (if --repo not provided)")
    parser.add_argument("--persist-store", action="store_true", help="Keep SQLite store after run")
    parser.add_argument("--store-path", default=None, help="Path to SQLite store (optional)")
    parser.add_argument("--metrics-out", default=None, help="Path to write metrics JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    repo_url, directory_path = configure_code_base_source(args.repo, args.directory, cache_dir="~/.cache/github")
    root = Path(directory_path)
    prompt_text = read_prompt_file(args.prompt)

    store_path = Path(args.store_path) if args.store_path else None
    store = Store(db_path=store_path, persist=args.persist_store)
    try:
        report, rv = run_pipeline(root, prompt_text, store, gate=None)
        expected_items = max(1, len(store.get_all_files()))
        metrics = evaluate_metrics(store, rv.id, expected_items=expected_items)  # type: ignore
        if args.metrics_out:
            Path(args.metrics_out).write_text(json.dumps(metrics, indent=2))
            print(f"Metrics written to {args.metrics_out}")
        else:
            print(json.dumps(metrics, indent=2))
    finally:
        store.close()


if __name__ == "__main__":
    main()
