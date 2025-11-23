# PRD: Proportional Complexity

## Problem Statement

Tech_writer currently uses static limits for documentation generation:
- `max_sections = 50`
- `max_exploration_steps = 500`

These limits don't adapt to the actual codebase being documented. A 100-line utility library gets the same budget as a 100,000-line monorepo, leading to:

1. **Over-documentation of small codebases** - Wasted tokens exploring simple code
2. **Under-documentation of large codebases** - Important modules missed due to budget exhaustion
3. **Inconsistent quality** - No principled basis for "how much is enough"

### The Core Issue

File count and lines of code are poor proxies for documentation effort. 100 templated HTML files may need less explanation than 10 complex algorithm implementations. We need a metric that captures both **size** and **complexity**.

## Solution

Integrate a **complexity analyzer** that measures Total Cyclomatic Complexity (Total CC) before documentation generation begins. This metric naturally combines codebase size and function complexity into a single number that scales with documentation effort.

### What is Total CC?

Total CC = Sum of cyclomatic complexity across all functions in the codebase.

- **Cyclomatic complexity** counts decision points (if, for, while, switch cases, boolean operators)
- **Summing across all functions** captures both size (more functions) and complexity (harder functions)

### Benchmark Data

| Repository | Files | Functions | Total CC | Bucket |
|------------|-------|-----------|----------|--------|
| axios/axios | 170 | 897 | 3,353 | simple |
| fastapi/fastapi | 1,189 | 3,971 | 12,626 | medium |
| openai/codex | 611 | 6,054 | 23,965 | medium |
| facebook/react | 4,360 | 43,241 | 152,308 | complex |

React requires ~45x more documentation effort than axios - and the metric reflects this.

## Requirements

### Functional Requirements

#### FR1: Pre-Analysis Phase
Before documentation generation begins:
1. Clone/update repository to local cache (if GitHub URL provided)
2. Run Rust complexity analyzer on the local copy
3. Parse JSON output to extract Total CC
4. Map Total CC to documentation budget

#### FR2: Complexity-Based Budget Mapping
Map Total CC to actionable documentation parameters:

| Total CC | Bucket | Max Sections | Max Exploration | Guidance |
|----------|--------|--------------|-----------------|----------|
| < 5,000 | simple | 10 | 100 | Cover all components thoroughly |
| 5,000-25,000 | medium | 25 | 300 | Focus on architecture and key modules |
| 25,000-100,000 | large | 40 | 500 | Prioritize core systems and hotspots |
| > 100,000 | complex | 50 | 800 | Strategic coverage of architecture and entry points |

#### FR3: Context Injection
Provide complexity context to the LLM:
- Complexity bucket and description
- Top 10 most complex functions (hotspots to cover)
- Explicit guidance on prioritization strategy
- Permission to "skip" low-value areas in large codebases

#### FR4: Graceful Fallback
If complexity analysis fails:
- Log warning
- Fall back to default limits
- Continue with documentation generation

### Non-Functional Requirements

#### NFR1: Performance
- Complexity analysis must complete in < 5 seconds for codebases up to 5,000 files
- Use Rust implementation for speed (6-33x faster than Python)

#### NFR2: Reliability
- Handle missing/corrupt files gracefully
- Respect .gitignore (don't analyze node_modules, __pycache__, etc.)

#### NFR3: Transparency
- Log complexity metrics at start of run
- Include complexity summary in final report metadata

## User Experience

### Before (Current)
```bash
python -m tech_writer --repo https://github.com/facebook/react
# Uses same limits as a tiny library
# May exhaust budget before covering core modules
```

### After (Proportional)
```bash
python -m tech_writer --repo https://github.com/facebook/react
# Analyzing complexity... Total CC: 152,308 (complex)
# Documentation budget: 50 sections, 800 exploration steps
# Prioritizing: architecture, core modules, top 10 complex functions
```

## Success Metrics

1. **Appropriate scaling** - Large codebases get more sections than small ones
2. **Hotspot coverage** - Top complex functions are documented
3. **No budget waste** - Small codebases don't over-explore
4. **Consistent quality** - Similar complexity = similar documentation depth

## Out of Scope (v1)

- Per-module complexity breakdown
- Historical complexity trends
- Complexity-based section ordering
- User override of complexity-derived limits

## Dependencies

- Rust complexity analyzer (`pocs/code-base-complexity/rust/`)
- Pre-built binary or build-on-demand capability
