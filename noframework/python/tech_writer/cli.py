"""
Command-line interface for tech_writer.

Usage:
    python -m tech_writer --prompt <file> --repo <path_or_url> [options]
"""

import argparse
import sys
from pathlib import Path

# Default values (must match orchestrator.py constants)
DEFAULT_MAX_EXPLORATION = 50
DEFAULT_MAX_SECTIONS = 20
DEFAULT_CACHE_FILENAME = ".tech_writer_cache.db"


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Generate technical documentation for a codebase.",
        prog="tech_writer",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Path to prompt file",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository path or GitHub URL",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--cache-dir",
        default="~/.cache/github",
        help="Directory for caching cloned repos",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.1",
        help="LLM model to use (e.g., gpt-5.1 for OpenAI, openai/gpt-5.1 for OpenRouter)",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "openrouter"],
        default="openai",
        help="LLM provider (default: openai)",
    )
    parser.add_argument(
        "--no-track-cost",
        action="store_true",
        help="Disable cost tracking (enabled by default for OpenRouter)",
    )
    parser.add_argument(
        "--base-url",
        help="Base URL for LLM API (overrides provider default)",
    )
    parser.add_argument(
        "--verify-citations",
        action="store_true",
        help="Verify and report on citation validity",
    )
    parser.add_argument(
        "--max-exploration",
        type=int,
        default=DEFAULT_MAX_EXPLORATION,
        help=f"Maximum exploration steps during Phase 1 (default: {DEFAULT_MAX_EXPLORATION})",
    )
    parser.add_argument(
        "--max-sections",
        type=int,
        default=DEFAULT_MAX_SECTIONS,
        help=f"Maximum sections in the outline (default: {DEFAULT_MAX_SECTIONS})",
    )
    parser.add_argument(
        "--persist-cache",
        action="store_true",
        help="Persist SQLite cache to disk for debugging",
    )
    parser.add_argument(
        "--cache-path",
        help=f"Path for persistent cache file (default: {DEFAULT_CACHE_FILENAME})",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO). Logs go to stderr and ~/.tech_writer/logs/",
    )

    args = parser.parse_args()

    # Read prompt file
    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"Error: Prompt file not found: {args.prompt}", file=sys.stderr)
        return 1

    prompt = prompt_path.read_text()

    # Run pipeline
    try:
        from tech_writer.orchestrator import run_pipeline

        # Determine cache path for persistence
        db_path = None
        if args.persist_cache:
            db_path = args.cache_path or DEFAULT_CACHE_FILENAME

        # Determine cost tracking setting
        track_cost = args.provider == "openrouter" and not args.no_track_cost

        report, store, cost_summary = run_pipeline(
            prompt=prompt,
            repo=args.repo,
            cache_dir=args.cache_dir,
            model=args.model,
            provider=args.provider,
            base_url=args.base_url,
            max_exploration=args.max_exploration,
            max_sections=args.max_sections,
            db_path=db_path,
            log_level=args.log_level,
            track_cost=track_cost,
        )

        # Report cost if tracked
        if cost_summary and cost_summary.total_cost_usd > 0:
            print(f"\nCost summary:", file=sys.stderr)
            print(f"  Provider: {cost_summary.provider}", file=sys.stderr)
            print(f"  Model: {cost_summary.model}", file=sys.stderr)
            print(f"  Total cost: ${cost_summary.total_cost_usd:.4f}", file=sys.stderr)
            print(f"  Total tokens: {cost_summary.total_tokens:,}", file=sys.stderr)
            print(f"  API calls: {cost_summary.total_calls}", file=sys.stderr)

        # Verify citations if requested
        if args.verify_citations:
            from tech_writer.citations import verify_all_citations

            results, valid, invalid = verify_all_citations(report, store)
            total = valid + invalid
            if total > 0:
                pct = valid / total * 100
                print(f"\nCitation verification:", file=sys.stderr)
                print(f"  Valid: {valid}/{total} ({pct:.0f}%)", file=sys.stderr)
                if invalid > 0:
                    print(f"  Invalid citations:", file=sys.stderr)
                    for r in results:
                        if not r.valid:
                            print(f"    - [{r.citation.path}:{r.citation.start_line}-{r.citation.end_line}]: {r.error}", file=sys.stderr)

        # Output report
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"Report written to: {args.output}", file=sys.stderr)
        else:
            print(report)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
