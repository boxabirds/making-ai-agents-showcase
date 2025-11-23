# Feature 3: Proportional Complexity

## Problem Statement

tech_writer currently uses static limits for documentation generation:
- `max_sections = 50`
- `max_exploration_steps = 500`

These limits don't adapt to the actual codebase being documented. A 100-line utility library gets the same budget as a 100,000-line monorepo, leading to:

1. **Over-documentation of small codebases** - Wasted tokens exploring simple code
2. **Under-documentation of large codebases** - Important modules missed due to budget exhaustion
3. **Inconsistent quality** - No principled basis for "how much is enough"

### The Core Issue

File count and lines of code are poor proxies for documentation effort. 100 templated HTML files may need less explanation than 10 complex algorithm implementations. We need a metric that captures both **size** and **complexity**.

### Benchmark Evidence

| Repository | Files | Functions | Total CC | Bucket |
|------------|-------|-----------|----------|--------|
| axios/axios | 170 | 897 | 3,353 | simple |
| fastapi/fastapi | 1,189 | 3,971 | 12,626 | medium |
| openai/codex | 611 | 6,054 | 23,965 | medium |
| facebook/react | 4,360 | 43,241 | 152,308 | complex |

React requires ~45x more documentation effort than axios. The metric must reflect this.

## User Stories

### US-3.1: Automatic Budget Scaling
As a developer, I want documentation depth to scale automatically with codebase complexity so that small repos don't waste tokens and large repos get adequate coverage.

### US-3.2: Complexity Visibility
As a team lead, I want to see the complexity metrics before documentation runs so that I can understand the expected effort.

### US-3.3: Hotspot Coverage
As a new team member, I want complex functions highlighted in documentation so that I can focus learning on the hardest parts.

### US-3.4: Dry Run Mode
As a developer, I want to preview complexity analysis without running the full pipeline so that I can validate the codebase before committing to a long run.

## Proposed Solution

Integrate a **Rust complexity analyzer** that measures Total Cyclomatic Complexity (Total CC) before documentation generation begins. This metric naturally combines codebase size and function complexity into a single number that scales with documentation effort.

### What is Total CC?

Total CC = Sum of cyclomatic complexity across all functions in the codebase.

- **Cyclomatic complexity** counts decision points (if, for, while, switch cases, boolean operators)
- **Summing across all functions** captures both size (more functions) and complexity (harder functions)

This aligns with [COCOMO](https://en.wikipedia.org/wiki/COCOMO) and industry-standard effort estimation: `Effort = Size x Complexity`

### Budget Mapping

| Total CC | Bucket | Max Sections | Max Exploration | Guidance |
|----------|--------|--------------|-----------------|----------|
| < 5,000 | simple | 10 | 100 | Cover all components thoroughly |
| 5,000-25,000 | medium | 25 | 300 | Focus on architecture and key modules |
| 25,000-100,000 | large | 40 | 500 | Prioritize core systems and hotspots |
| > 100,000 | complex | 50 | 800 | Strategic coverage of architecture and entry points |

### Context Injection

The LLM receives:
- Complexity bucket and description
- Top 10 most complex functions (hotspots to cover)
- Explicit guidance on prioritization strategy
- Permission to "skip" low-value areas in large codebases

## Success Criteria

- [ ] Complexity analysis runs automatically after repo resolution
- [ ] Budget (sections, exploration steps) scales with Total CC
- [ ] Top complex functions are surfaced to the LLM
- [ ] `--dry-run` flag shows complexity analysis without running pipeline
- [ ] `--skip-complexity` flag allows bypassing analysis
- [ ] Complexity metrics appear in logs and final report metadata
- [ ] Analysis completes in < 5 seconds for codebases up to 5,000 files

## Out of Scope

- Per-module complexity breakdown
- Historical complexity trends
- Complexity-based section ordering
- User override of complexity-derived limits
- Automatic model selection based on complexity

## Dependencies

- Rust complexity analyzer (`tools/complexity-analyzer/`)
- Rust toolchain for building (or pre-built binary)
- Working git installation (for cloning repos)

## Risks

| Risk | Mitigation |
|------|------------|
| Rust binary not found | Graceful fallback to defaults, log warning |
| Analysis timeout on huge repos | 5-minute timeout, fall back to defaults |
| JavaScript grammar variance | Accept variance, focus on bucket classification |
| Build complexity for users | Document build steps, consider pre-built binaries |

## Technical References

- Complexity analyzer: `tools/complexity-analyzer/`
- Benchmarks: `docs/reports/20251123-1851-complexity-benchmarks.md`
- POC (Python reference): `pocs/code-base-complexity/`
