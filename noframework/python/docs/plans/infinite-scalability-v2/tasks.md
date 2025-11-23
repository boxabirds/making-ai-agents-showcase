# Implementation Tasks: Infinite-Scalability Tech Writer v2

Reference repo: `https://github.com/axios/axios`
Reference prompt: `prompts/architecture-overview-lite.prompt.txt`

## Status

| # | Task | Status | Dependencies |
|---|------|--------|--------------|
| 1 | Project scaffolding | ✅ done | - |
| 2 | SQLite cache store | ✅ done | 1 |
| 3 | list_files tool | ✅ done | 2 |
| 4 | read_file tool (basic) | ✅ done | 3 |
| 5 | Tree-sitter parser setup | ✅ done | 4 |
| 6 | Symbol extraction | ✅ done | 5 |
| 7 | Import extraction | ✅ done | 6 |
| 8 | get_symbols tool | ✅ done | 6 |
| 9 | get_imports tool | ✅ done | 7 |
| 10 | get_definition tool | ✅ done | 8 |
| 11 | get_references tool | ✅ done | 8 |
| 12 | get_structure tool | ✅ done | 8, 9 |
| 13 | search_text tool (FTS) | ⚠️ partial | 2 |
| 14 | Tool registration (OpenAI format) | ✅ done | 3, 4, 8-13 |
| 15 | Exploration orchestration | ✅ done | 14 |
| 16 | finish_exploration handling | ✅ done | 15 |
| 17 | Outline generation | ✅ done | 16 |
| 18 | Section generation (agentic) | ⚠️ partial | 17 |
| 19 | Citation parsing | ✅ done | 4 |
| 20 | Citation verification | ✅ done | 19 |
| 21 | Report assembly | ✅ done | 18, 20 |
| 22 | CLI implementation | ⚠️ partial | 21 |
| 23 | Remote repo cloning | ✅ done | 22 |
| 24 | BDD test framework setup | ✅ done | 1 |
| 25 | Feature: exploration tools | ✅ done | 24, 14 |
| 26 | Feature: semantic queries | ✅ done | 25 |
| 27 | Feature: outline generation | ✅ done | 26 |
| 28 | Feature: section generation | ✅ done | 27 |
| 29 | Feature: citation verification | ✅ done | 28 |
| 30 | E2E: axios + architecture-overview-lite | ⚠️ partial | 29, 23 |
| 31 | Make section generation agentic | 🔲 todo | 18 |
| 32 | Add CLI control flags | 🔲 todo | 22, 31 |
| 33 | Implement FTS5 in CacheStore | 🔲 todo | 2 |
| 34 | Citation re-generation | 🔲 todo | 20, 31 |
| 35 | E2E integration test | 🔲 todo | 31, 32, 34 |

## Phases

### Phase 1: Foundation (Tasks 1-4)
Basic project structure, storage, and file system access.

### Phase 2: Tree-sitter Integration (Tasks 5-7)
Parsing infrastructure for semantic queries.

### Phase 3: Semantic Tools (Tasks 8-13)
Complete tool suite for agentic exploration.

### Phase 4: Orchestration (Tasks 14-18)
Exploration loop, outline, and section generation.

### Phase 5: Citations & Assembly (Tasks 19-21)
Citation system and report assembly.

### Phase 6: CLI & Integration (Tasks 22-23)
User-facing interface and remote repo support.

### Phase 7: BDD Testing (Tasks 24-30)
Behavior-driven tests using axios as reference.

### Phase 8: Bug Fixes & Completion (Tasks 31-35)
Address gaps identified in 2025-11-23 audit.

**Critical:**
- Task 31: Section generation is not agentic (design spec violation)

**High:**
- Task 32: CLI missing `--max-exploration`, `--max-sections`, `--persist-cache`
- Task 33: FTS5 not implemented (`store.search()` raises NotImplementedError)

**Medium:**
- Task 34: Invalid citations should trigger section re-generation
- Task 35: No E2E integration tests exist

## Execution Order

Tasks 31-35 should be executed in this order:

1. **Task 31** (Make section generation agentic) - Critical fix, no new dependencies
2. **Task 33** (FTS5) - Independent, can be done in parallel with 31
3. **Task 32** (CLI flags) - Depends on 31 for `max_exploration` to affect sections
4. **Task 34** (Citation re-generation) - Depends on 31 for agentic re-generation
5. **Task 35** (E2E tests) - Depends on 31, 32, 34 to test complete functionality

```
     ┌──────────┐
     │ Task 31  │ ◄── Critical: agentic sections
     └────┬─────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌──────────┐ ┌──────────┐
│ Task 32  │ │ Task 34  │
│ CLI flags│ │ Citation │
└────┬─────┘ │ re-gen   │
     │       └────┬─────┘
     │            │
     └─────┬──────┘
           │
           ▼
     ┌──────────┐
     │ Task 35  │
     │ E2E tests│
     └──────────┘

Task 33 (FTS5) is independent - can be done anytime.
```
