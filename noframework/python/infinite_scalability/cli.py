import argparse
from datetime import datetime
from pathlib import Path

from common.utils import configure_code_base_source, read_prompt_file, save_results

from .orchestrator import run_pipeline
from .ingest import ingest_repo
from .store import Store
from .models import ReportVersionRecord
from .summarize import summarize_all_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Infinite scalability tech writer (skeleton).")
    parser.add_argument("directory", nargs="?", help="Directory to analyze (ignored if --repo is provided)")
    parser.add_argument("--repo", help="GitHub repo URL (e.g., https://github.com/axios/axio)")
    parser.add_argument("--prompt", required=True, help="Path to prompt file containing the tech brief")
    parser.add_argument("--persist-store", action="store_true", help="Keep the SQLite store after run")
    parser.add_argument("--store-path", default=None, help="Optional explicit path for the SQLite store")
    parser.add_argument("--output-dir", default="output", help="Directory to write the markdown report")
    parser.add_argument("--file-name", default=None, help="Override output file name")
    parser.add_argument("--model", default=None, help="Model name (placeholder, not yet used)")
    return parser.parse_args()


def generate_skeleton_report(root: Path, file_count: int, chunk_count: int, prompt: str) -> str:
    timestamp = datetime.utcnow().isoformat()
    return "\n".join(
        [
            f"# Tech Writer Report (Skeleton)",
            f"- Generated: {timestamp} UTC",
            f"- Target: `{root}`",
            f"- Prompt summary: {prompt[:200]}{'...' if len(prompt) > 200 else ''}",
            "",
            "## Inventory",
            f"- Files ingested: {file_count}",
            f"- Chunks ingested: {chunk_count}",
            "",
            "_Note: full analysis pending implementation of summarization, retrieval, and verification._",
        ]
    )


def main():
    args = parse_args()
    repo_url, directory_path = configure_code_base_source(args.repo, args.directory, cache_dir="~/.cache/github")
    root = Path(directory_path)
    prompt_text = read_prompt_file(args.prompt)

    store_path = Path(args.store_path) if args.store_path else None
    store = Store(db_path=store_path, persist=args.persist_store)

    try:
        # Run minimal pipeline (placeholder for full DSPy/LLM flow)
        report_md, rv = run_pipeline(root, prompt_text, store)
        output_file = save_results(
            analysis_result=report_md,
            model_name=args.model or "skeleton",
            repo_name=root.name,
            output_dir=args.output_dir,
            extension=".md",
            file_name=args.file_name,
        )

        print(f"Report written to: {output_file}")
        if args.persist_store:
            print(f"Store retained at: {store.db_path}")
        else:
            print("Ephemeral store will be deleted.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
