# PRD: Codebase Complexity Analyzer

## Overview

A tool to assess codebase complexity using tree-sitter AST analysis, providing language-agnostic metrics that help scale documentation effort proportionally to actual code complexity.

## Problem Statement

Current tech_writer uses static limits (max_sections, max_exploration) that don't adapt to codebase complexity. A 100-line utility and a 100k-line monorepo get similar treatment unless manually configured.

**Key insight:** File count and LOC are poor proxies for complexity. 100 templated HTML files may be simpler than 10 algorithm implementations.

## Goals

1. **Measure actual complexity** using tree-sitter AST analysis
2. **Language-agnostic metrics** via normalized AST concepts
3. **Respect .gitignore** to exclude generated/vendored code
4. **Fast execution** - complete in seconds for large repos
5. **Dual implementation** - Python for integration with tech_writer, Rust for performance comparison

## Success Metrics

- Process axios repo (~160 JS files) in < 5 seconds
- Process fastapi repo (~200 Python files) in < 5 seconds
- Produce consistent metrics between Python and Rust implementations
- Correctly identify high-complexity outlier functions

## Requirements

### Functional Requirements

#### FR1: File Discovery
- Walk repository respecting .gitignore
- Filter by known source extensions
- Skip binary files
- Support local paths and GitHub URLs

#### FR2: Language Detection
- Map file extensions to tree-sitter languages
- Support: Python, JavaScript, TypeScript, Go, Rust, Java, C, C++

#### FR3: AST Parsing
- Parse source files with tree-sitter
- Handle parse failures gracefully
- Track parse success rate

#### FR4: Complexity Metrics

**Per-function metrics:**
- Cyclomatic complexity: `1 + decision_points`
- Cognitive complexity: cyclomatic + nesting penalty
- Max nesting depth
- Lines of code
- Parameter count

**Per-file metrics:**
- Total functions/classes
- Average/max function complexity
- Parse status (success/failure)

**Per-repo metrics:**
- Total files by language
- Total symbols (functions, classes)
- Complexity distribution (histogram)
- Top N most complex functions
- Aggregate complexity score

#### FR5: Output Format
```json
{
  "repository": "axios/axios",
  "scan_time_ms": 1234,
  "summary": {
    "total_files": 161,
    "total_functions": 487,
    "languages": {"javascript": 145, "typescript": 16},
    "complexity_score": 42.5,
    "complexity_bucket": "medium"
  },
  "distribution": {
    "low": 320,      // complexity 1-5
    "medium": 142,   // complexity 6-15
    "high": 25       // complexity > 15
  },
  "top_complex_functions": [
    {"file": "lib/core/Axios.js", "name": "request", "complexity": 28, "line": 45}
  ]
}
```

### Non-Functional Requirements

#### NFR1: Performance
- < 5 seconds for repos with < 500 source files
- Memory usage < 500MB

#### NFR2: Accuracy
- Python and Rust implementations produce identical complexity scores for same input

#### NFR3: Portability
- Python: Works with existing tech_writer dependencies
- Rust: Standalone binary, reuses ../rust/ patterns

## Out of Scope (v1)

- Semantic complexity (call graph analysis)
- Cross-file dependency analysis
- Historical complexity trends
- IDE integration

## Test Repositories

1. **axios/axios** - Medium JS library (~160 files)
2. **fastapi/fastapi** - Medium Python framework (~200 files)

## Implementation Phases

### Phase 1: Core Metrics (This POC)
- File discovery with .gitignore
- Tree-sitter parsing
- Cyclomatic complexity calculation
- JSON output

### Phase 2: Integration (Future)
- Integrate into tech_writer orchestrator
- Dynamic limit adjustment based on complexity score
- Complexity context in LLM prompts
