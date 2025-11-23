# Feature 3: Proportional Complexity - Task Plan

## Overview

Implementation tasks for complexity-based documentation budgets.

## Task Summary

| ID | Task | Status | Dependencies |
|----|------|--------|--------------|
| 3-1 | Create complexity.py module | pending | - |
| 3-2 | Add unit tests for complexity module | pending | 3-1 |
| 3-3 | Add CLI flags (--skip-complexity, --dry-run) | pending | 3-1 |
| 3-4 | Integrate complexity budget into orchestrator | pending | 3-1, 3-3 |
| 3-5 | Add context injection to LLM prompts | pending | 3-4 |
| 3-6 | Add complexity to report metadata | pending | 3-4 |
| 3-7 | Implement build-on-demand and Python fallback | pending | 3-1 |
| 3-8 | Add integration tests | pending | 3-4 |
| 3-9 | Add BDD feature tests | pending | 3-8 |

## Task Details

### 3-1: Create complexity.py module

Create `tech_writer/complexity.py` with dataclasses and core functions.

See: `docs/designs/3/tech-design.md` §Python Integration

---

### 3-2: Add unit tests for complexity module

Create `tests/tech_writer/test_complexity.py` with unit tests.

See: `docs/designs/3/tech-design.md` §Testing

---

### 3-3: Add CLI flags

Add `--skip-complexity` and `--dry-run` flags to CLI.

See: `docs/designs/3/tech-design.md` §CLI Integration

---

### 3-4: Integrate complexity budget into orchestrator

Update `run_pipeline()` to accept and use `ComplexityBudget`.

See: `docs/designs/3/tech-design.md` §Orchestrator Integration

---

### 3-5: Add context injection to LLM prompts

Inject complexity context into exploration and outline prompts.

See: `docs/designs/3/tech-design.md` §Context Injection

---

### 3-6: Add complexity to report metadata

Include complexity metrics in metadata JSON output.

See: `docs/designs/3/tech-design.md` §Report Metadata

---

### 3-7: Implement build-on-demand and Python fallback

Add `ensure_analyzer_built()` and fallback to Python analyzer.

See: `docs/designs/3/tech-design.md` §Binary Distribution Options

---

### 3-8: Add integration tests

Test against real repositories (axios, fastapi, react).

See: `docs/designs/3/tech-design.md` §Integration Tests

---

### 3-9: Add BDD feature tests

Create `tests/features/test_complexity_bdd.py`.

See: `docs/designs/3/tech-design.md` §Testing
