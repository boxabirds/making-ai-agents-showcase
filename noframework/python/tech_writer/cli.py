"""
Command-line interface for tech_writer.

Usage:
    python -m tech_writer --prompt <file> --repo <path_or_url> [options]
"""

import argparse
import sys
from pathlib import Path


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
        default="gpt-4o",
        help="LLM model to use",
    )
    parser.add_argument(
        "--base-url",
        help="Base URL for LLM API",
    )
    parser.add_argument(
        "--verify-citations",
        action="store_true",
        help="Verify and report on citation validity",
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

        report, store = run_pipeline(
            prompt=prompt,
            repo=args.repo,
            cache_dir=args.cache_dir,
            model=args.model,
            base_url=args.base_url,
        )

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
