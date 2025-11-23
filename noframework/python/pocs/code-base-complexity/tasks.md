# Tasks: Codebase Complexity Analyzer POC

> **Note**: This POC has been promoted to Feature 3: Proportional Complexity.
> - Feature docs: `docs/features/3/`
> - Rust analyzer: `tools/complexity-analyzer/`
> - Python implementation remains here as reference/fallback.

## Phase 1: Python Implementation

### P1.1: File Discovery with .gitignore Support
- [x] Create `complexity_analyzer.py` with main structure
- [x] Implement `discover_files()` using pathspec for .gitignore
- [x] Add extension → language mapping
- [x] Add binary file detection and skipping
- [x] Test: List files from local directory respecting .gitignore

### P1.2: Node Mapping Definition
- [x] Create `normalized_nodes.py` with node type mappings
- [x] Define UN_Function, UN_If, UN_Loop, UN_Switch, UN_BooleanOp for:
  - Python
  - JavaScript
  - TypeScript
  - Go, Rust, Java (bonus)
- [x] Add helper functions: `is_function_node()`, `is_decision_point()`

### P1.3: Tree-sitter Integration
- [x] Parse files with tree-sitter-languages
- [x] Handle parse failures gracefully
- [x] Extract function nodes from AST
- [x] Test: Parse sample Python and JS files

### P1.4: Complexity Calculation
- [x] Implement `calculate_cyclomatic_complexity()`
- [x] Implement `calculate_cognitive_complexity()` with nesting penalty
- [x] Implement `calculate_max_nesting_depth()`
- [x] Test: Verify complexity scores on known functions

### P1.5: Aggregation & Output
- [x] Aggregate per-file metrics
- [x] Aggregate per-repo metrics
- [x] Generate JSON output format
- [x] Add complexity bucket classification
- [x] Test: Full pipeline on small repo

### P1.6: GitHub Integration
- [x] Add support for GitHub URLs (reuse tech_writer.repo)
- [x] Clone/update repos to cache directory
- [x] Test: Analyze axios from GitHub URL

---

## Phase 2: Rust Implementation

### R2.1: Project Setup
- [x] Create `rust/` directory with Cargo.toml
- [x] Add dependencies: tree-sitter, ignore, rayon, serde, clap
- [x] Copy .gitignore walking pattern from ../rust/main.rs
- [x] Copy clone_or_update_repo from ../rust/main.rs

### R2.2: File Discovery
- [x] Implement file walking with `ignore` crate
- [x] Add extension filtering
- [x] Test: List files matching Python implementation

### R2.3: Tree-sitter Integration
- [x] Add tree-sitter language crates (python, javascript, typescript)
- [x] Implement parser selection by language
- [x] Handle parse failures

### R2.4: Node Mapping
- [x] Port normalized_nodes mapping to Rust
- [x] Implement `is_function_node()`, `is_decision_point()`

### R2.5: Complexity Calculation
- [x] Port cyclomatic complexity algorithm
- [x] Port cognitive complexity algorithm
- [x] Verify identical results to Python (✓ on Python code, see note below)

### R2.6: Parallel Processing
- [x] Add rayon for parallel file processing
- [x] Aggregate results thread-safely
- [x] Benchmark: Compare single-threaded vs parallel

### R2.7: Output & CLI
- [x] Match JSON output format exactly
- [x] Add clap CLI with same interface as Python
- [x] Test: Run on same repos as Python

---

## Phase 3: Comparison & Validation

### V3.1: Comparison Script
- [x] Create `run_comparison.sh`
- [x] Run Python on axios → output_py.json
- [x] Run Rust on axios → output_rs.json
- [x] Compare outputs programmatically
- [x] Report timing differences

### V3.2: Test Repositories
- [x] Test on axios/axios (JavaScript) - see findings below
- [x] Test on fastapi/fastapi (Python) - 99.97% match (3971 vs 3972 functions)
- [x] Verify results match between implementations (Python code: ✓)
- [x] Document any discrepancies (see findings below)

### V3.3: Performance Benchmarking
- [x] Measure Python time: ~1123ms on local repo, ~358ms on axios, ~4927ms on fastapi
- [x] Measure Rust time: ~18ms on local repo, ~41ms on axios, ~809ms on fastapi
- [x] Document findings: Rust is ~60x faster on small repos, ~9x on axios, ~6x on fastapi

---

## Findings & Known Issues

### JavaScript Parser Discrepancy

When analyzing JavaScript repos (axios), Python and Rust report different function counts:
- Python (tree-sitter-languages): 897 functions
- Rust (tree-sitter-javascript v0.21): 2204 functions

**Root cause**: Different tree-sitter parser versions. The Python `tree-sitter-languages` package bundles different grammar versions than the individual Rust crates.

**Impact**: Function counts differ, but both implementations:
- Find the same source files (170 files)
- Detect the same language breakdown (164 JS, 6 TS)
- Classify complexity bucket consistently ("simple")
- Respect .gitignore correctly

**Mitigation options**:
1. Pin to identical tree-sitter versions (requires compiling grammars manually)
2. Accept variance and focus on relative complexity rankings
3. Use only one implementation (Python for simplicity, Rust for speed)

### Python Code Analysis: Near-Perfect Match

On Python codebases (fastapi - 1189 files), implementations produce nearly identical results:
- Same file counts: 1189 ✓
- Same function counts: 3971 vs 3972 (diff due to 3 JS files)
- Same complexity score: 3.38 ✓
- Same top functions: jsonable_encoder (CC=36), analyze_param (CC=36), get_openapi_path (CC=33)

The 1-function difference is from 3 JavaScript files using different tree-sitter versions.
This validates that the algorithms are correct; JS grammar variance is the only source of discrepancy.

---

## Phase 4: Integration Preparation (Future)

### I4.1: tech_writer Integration Points
- [ ] Design `ComplexityAnalyzer` class for orchestrator
- [ ] Define complexity → budget mapping
- [ ] Add complexity context to exploration prompts

### I4.2: Documentation
- [x] Update PRD with findings
- [x] Document edge cases and limitations
- [ ] Create usage examples

---

## Test Commands

```bash
# Python
python complexity_analyzer.py --repo https://github.com/axios/axios
python complexity_analyzer.py --path /path/to/local/repo

# Rust
cd rust && cargo run --release -- --repo https://github.com/axios/axios
cd rust && cargo run --release -- --path /path/to/local/repo

# Comparison
./run_comparison.sh https://github.com/axios/axios
./run_comparison.sh https://github.com/fastapi/fastapi
```

## Acceptance Criteria

1. **Correctness**: Python and Rust produce identical complexity scores on Python code ✓
2. **Performance**: Both complete axios analysis in < 5 seconds ✓ (Python: 358ms, Rust: 41ms)
3. **.gitignore**: Neither implementation counts files in node_modules, __pycache__, etc. ✓
4. **Output**: JSON format matches specification in PRD ✓
5. **Top functions**: Results match on Python codebases; JS variance due to grammar versions
