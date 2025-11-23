# Implementation Tasks: Infinite-Scalability Tech Writer v2

Reference repo: `https://github.com/axios/axios`
Reference prompt: `prompts/architecture-overview-lite.prompt.txt`

## Status

| # | Task | Status | Dependencies |
|---|------|--------|--------------|
| 1 | Project scaffolding | pending | - |
| 2 | SQLite cache store | pending | 1 |
| 3 | list_files tool | pending | 2 |
| 4 | read_file tool (basic) | pending | 3 |
| 5 | Tree-sitter parser setup | pending | 4 |
| 6 | Symbol extraction | pending | 5 |
| 7 | Import extraction | pending | 6 |
| 8 | get_symbols tool | pending | 6 |
| 9 | get_imports tool | pending | 7 |
| 10 | get_definition tool | pending | 8 |
| 11 | get_references tool | pending | 8 |
| 12 | get_structure tool | pending | 8, 9 |
| 13 | search_text tool (FTS) | pending | 2 |
| 14 | Tool registration (OpenAI format) | pending | 3, 4, 8-13 |
| 15 | Exploration orchestration | pending | 14 |
| 16 | finish_exploration handling | pending | 15 |
| 17 | Outline generation | pending | 16 |
| 18 | Section generation (agentic) | pending | 17 |
| 19 | Citation parsing | pending | 4 |
| 20 | Citation verification | pending | 19 |
| 21 | Report assembly | pending | 18, 20 |
| 22 | CLI implementation | pending | 21 |
| 23 | Remote repo cloning | pending | 22 |
| 24 | BDD test framework setup | pending | 1 |
| 25 | Feature: exploration tools | pending | 24, 14 |
| 26 | Feature: semantic queries | pending | 25 |
| 27 | Feature: outline generation | pending | 26 |
| 28 | Feature: section generation | pending | 27 |
| 29 | Feature: citation verification | pending | 28 |
| 30 | E2E: axios + architecture-overview-lite | pending | 29, 23 |

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
