# Tasks: Proportional Complexity

## Priority: HIGH

This feature enables documentation to scale proportionally with codebase complexity.

---

## Phase 1: Complexity Module

### 1.1 Create `tech_writer/complexity.py`
- [ ] Define `ComplexityBudget` dataclass
- [ ] Implement `get_analyzer_path()` - find Rust binary
- [ ] Implement `analyze_complexity(repo_path)` - run analyzer, parse JSON
- [ ] Implement `map_complexity_to_budget(analysis)` - Total CC → budget
- [ ] Implement `get_complexity_context(budget)` - generate LLM context string
- [ ] Add constants: `BUCKET_SIMPLE_MAX`, `BUCKET_MEDIUM_MAX`, `BUCKET_LARGE_MAX`

### 1.2 Unit Tests
- [ ] Test bucket mapping at boundary values
- [ ] Test graceful handling of missing analyzer
- [ ] Test JSON parsing with sample outputs
- [ ] Test context string generation

---

## Phase 2: CLI Integration

### 2.1 Update `tech_writer/cli.py`
- [ ] Import complexity module
- [ ] Add `--skip-complexity` flag (for debugging/speed)
- [ ] Call `analyze_complexity()` after repo resolution
- [ ] Log complexity metrics to stderr
- [ ] Pass `ComplexityBudget` to `run_pipeline()`

### 2.2 Dry Run Mode
- [ ] Add `--dry-run` flag that shows complexity analysis without running pipeline
- [ ] Display: bucket, max_sections, max_exploration, top functions

---

## Phase 3: Orchestrator Integration

### 3.1 Update `run_pipeline()` signature
- [ ] Add `complexity_budget: Optional[ComplexityBudget]` parameter
- [ ] Use budget values for `max_sections`, `max_exploration_steps`, `section_max_steps`
- [ ] Fall back to defaults when budget is None

### 3.2 Context Injection
- [ ] Inject complexity context into exploration phase system prompt
- [ ] Inject complexity context into outline generation prompt
- [ ] Include top complex functions in section prioritization

### 3.3 Report Metadata
- [ ] Include complexity metrics in final report metadata
- [ ] Add "Complexity Analysis" section to report header

---

## Phase 4: Rust Analyzer Availability

### 4.1 Build-on-Demand (Development)
- [ ] Implement `ensure_analyzer_built()` function
- [ ] Check for cargo availability
- [ ] Build if binary missing
- [ ] Cache build status to avoid repeated checks

### 4.2 Fallback to Python
- [ ] If Rust unavailable, use Python analyzer
- [ ] Log performance warning
- [ ] Ensure output format matches

### 4.3 Documentation
- [ ] Update README with complexity analyzer setup
- [ ] Document `--skip-complexity` flag
- [ ] Add troubleshooting for Rust build issues

---

## Phase 5: Testing & Validation

### 5.1 Integration Tests
- [ ] Test axios (simple) → verify 10 sections limit
- [ ] Test fastapi (medium) → verify 25 sections limit
- [ ] Test react (complex) → verify 50 sections limit
- [ ] Test fallback when analyzer unavailable

### 5.2 E2E Validation
- [ ] Run full documentation on axios, verify proportional output
- [ ] Run full documentation on fastapi, verify proportional output
- [ ] Compare output quality vs fixed-budget runs

---

## Acceptance Criteria

1. **Automatic scaling**: Large codebases get more sections/steps than small ones
2. **Hotspot coverage**: Top complex functions appear in documentation
3. **Graceful degradation**: Missing analyzer doesn't break pipeline
4. **Performance**: Complexity analysis adds < 5s to pipeline
5. **Transparency**: Complexity metrics visible in logs and report

---

## Dependencies

- Rust toolchain (for building analyzer)
- `tools/complexity-analyzer/` (analyzer source)
- Working git installation (for cloning repos)

---

## Test Commands

```bash
# Build the Rust analyzer
cd tools/complexity-analyzer && cargo build --release

# Test complexity analysis standalone
./tools/complexity-analyzer/target/release/complexity-analyzer \
  --path /path/to/repo

# Test dry-run mode (after implementation)
python -m tech_writer --repo https://github.com/axios/axios --dry-run

# Full pipeline with complexity
python -m tech_writer --repo https://github.com/axios/axios

# Skip complexity analysis
python -m tech_writer --repo https://github.com/axios/axios --skip-complexity
```
