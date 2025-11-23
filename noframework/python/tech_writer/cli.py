"""
Command-line interface for tech_writer.

Usage:
    python -m tech_writer --prompt <file> --repo <path_or_url> [options]
"""

import argparse
import sys
from pathlib import Path

from tech_writer.orchestrator import DEFAULT_MAX_STEPS, DEFAULT_MAX_SECTIONS

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
        default=DEFAULT_MAX_STEPS,
        help=f"Maximum exploration steps during Phase 1 (default: {DEFAULT_MAX_STEPS})",
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
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="Generate metadata JSON file alongside output (requires --output)",
    )
    parser.add_argument(
        "--skip-complexity",
        action="store_true",
        help="Skip complexity analysis (use default budgets)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show complexity analysis without running pipeline",
    )

    args = parser.parse_args()

    # Validate --metadata requires --output
    if args.metadata and not args.output:
        parser.error("--metadata requires --output")

    # Read prompt file
    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"Error: Prompt file not found: {args.prompt}", file=sys.stderr)
        return 1

    prompt = prompt_path.read_text()

    # Resolve repository path
    from tech_writer.repo import resolve_repo

    try:
        repo_path, _is_remote = resolve_repo(args.repo, args.cache_dir)
    except Exception as e:
        print(f"Error resolving repository: {e}", file=sys.stderr)
        return 1

    # Run complexity analysis (unless skipped)
    complexity_budget = None
    if not args.skip_complexity:
        from tech_writer.complexity import (
            analyze_complexity,
            map_complexity_to_budget,
            get_complexity_context,
        )

        print("Analyzing codebase complexity...", file=sys.stderr)
        analysis = analyze_complexity(repo_path)

        if analysis:
            complexity_budget = map_complexity_to_budget(analysis)
            print(f"Complexity: {complexity_budget.total_cc:,} Total CC ({complexity_budget.bucket})", file=sys.stderr)
            print(f"Budget: {complexity_budget.max_sections} sections, {complexity_budget.max_exploration_steps} exploration steps", file=sys.stderr)

            # Show top complex functions
            if complexity_budget.top_functions:
                print("Top complex functions:", file=sys.stderr)
                for func in complexity_budget.top_functions[:5]:
                    print(f"  - {func.get('file', '?')}:{func.get('line', '?')} {func.get('name', '?')} (CC={func.get('cyclomatic_complexity', '?')})", file=sys.stderr)
        else:
            print("Complexity analysis unavailable, using defaults", file=sys.stderr)

    # Dry run: show analysis and exit
    if args.dry_run:
        if complexity_budget:
            print("\n" + get_complexity_context(complexity_budget), file=sys.stderr)
        print("\nDry run complete. No pipeline execution.", file=sys.stderr)
        return 0

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
            complexity_budget=complexity_budget,
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
        citation_results = None
        citation_valid = 0
        citation_invalid = 0
        if args.verify_citations:
            from tech_writer.citations import verify_all_citations

            citation_results, citation_valid, citation_invalid = verify_all_citations(report, store)
            total = citation_valid + citation_invalid
            if total > 0:
                pct = citation_valid / total * 100
                print(f"\nCitation verification:", file=sys.stderr)
                print(f"  Valid: {citation_valid}/{total} ({pct:.0f}%)", file=sys.stderr)
                if citation_invalid > 0:
                    print(f"  Invalid citations:", file=sys.stderr)
                    for r in citation_results:
                        if not r.valid:
                            print(f"    - [{r.citation.path}:{r.citation.start_line}-{r.citation.end_line}]: {r.error}", file=sys.stderr)

        # Output report
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"Report written to: {args.output}", file=sys.stderr)

            # Generate metadata if requested
            if args.metadata:
                from tech_writer.metadata import (
                    create_metadata,
                    CitationStats,
                    InvalidCitation,
                    CostInfo,
                    ComplexityInfo,
                )

                # Build citation stats if verification was run
                citation_stats = None
                if args.verify_citations and citation_results is not None:
                    citation_stats = CitationStats(
                        total=citation_valid + citation_invalid,
                        valid=citation_valid,
                        invalid=citation_invalid,
                        invalid_citations=[
                            InvalidCitation(
                                path=r.citation.path,
                                start_line=r.citation.start_line,
                                end_line=r.citation.end_line,
                                error=r.error,
                            )
                            for r in citation_results
                            if not r.valid
                        ],
                    )

                # Build cost info if available
                cost_info = None
                if cost_summary and cost_summary.total_cost_usd > 0:
                    cost_info = CostInfo(
                        total_cost_usd=cost_summary.total_cost_usd,
                        total_tokens=cost_summary.total_tokens,
                        total_calls=cost_summary.total_calls,
                        provider=cost_summary.provider,
                        model=cost_summary.model,
                    )

                # Build complexity info if available
                complexity_info = None
                if complexity_budget:
                    complexity_info = ComplexityInfo(
                        total_cc=complexity_budget.total_cc,
                        bucket=complexity_budget.bucket,
                        max_sections=complexity_budget.max_sections,
                        max_exploration_steps=complexity_budget.max_exploration_steps,
                        top_functions=complexity_budget.top_functions,
                    )

                metadata_path = create_metadata(
                    output_file=output_path,
                    model=args.model,
                    repo_path=args.repo,
                    prompt_file=args.prompt,
                    citations=citation_stats,
                    cost=cost_info,
                    complexity=complexity_info,
                )
                print(f"Metadata written to: {metadata_path}", file=sys.stderr)
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
