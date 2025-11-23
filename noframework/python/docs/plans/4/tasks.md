# Feature 4: Claude Code Prompt Enrichment - Task Plan

## Overview

Implementation tasks for pre-indexed code context injection via Claude Code hooks.

## Task Summary

| ID | Task | Status | Dependencies |
|----|------|--------|--------------|
| 4-1 | Create index module structure and types | pending | - |
| 4-2 | Implement SQLite schema and migrations | pending | 4-1 |
| 4-3 | Implement tree-sitter parser with Python queries | pending | 4-1 |
| 4-4 | Add tree-sitter queries for remaining languages | pending | 4-3 |
| 4-5 | Implement IndexBuilder | pending | 4-2, 4-3 |
| 4-6 | Implement QueryEngine | pending | 4-2 |
| 4-7 | Add unit tests for index module | pending | 4-5, 4-6 |
| 4-8 | Implement SessionStart hook | pending | 4-5 |
| 4-9 | Implement UserPromptSubmit hook | pending | 4-6 |
| 4-10 | Implement PostToolUse hook | pending | 4-5 |
| 4-11 | Implement file watcher | pending | 4-5 |
| 4-12 | Implement SessionEnd hook | pending | 4-11 |
| 4-13 | Add integration tests | pending | 4-8, 4-9, 4-10 |
| 4-14 | Add BDD feature tests | pending | 4-13 |
| 4-15 | Create installation script and documentation | pending | 4-14 |

## Task Details

### 4-1: Create index module structure and types

Create the module structure and dataclass definitions.

**Files to create**:
- `tech_writer/index/__init__.py`
- `tech_writer/index/types.py`

See: `docs/designs/4/tech-design.md` §2.2 Python Types

**Tests**: N/A (type definitions only)

---

### 4-2: Implement SQLite schema and migrations

Create schema management with table creation and indexes.

**Files to create**:
- `tech_writer/index/schema.py`

See: `docs/designs/4/tech-design.md` §2.1 SQLite Schema

**Tests**:
- Schema creates all tables
- Indexes exist
- FTS5 virtual table works

---

### 4-3: Implement tree-sitter parser with Python queries

Implement CodeParser class with Python language support.

**Files to create**:
- `tech_writer/index/parser.py`
- `tech_writer/index/queries/python.scm`

See: `docs/designs/4/tech-design.md` §3.1.3 Parser Interface, §4.2 Python Queries

**Tests**:
- Parses Python functions
- Parses Python classes
- Parses Python methods
- Parses Python imports (all forms)
- Handles syntax errors gracefully

---

### 4-4: Add tree-sitter queries for remaining languages

Add query files for JavaScript, TypeScript, Go, Rust, Ruby, Java, PHP, C++.

**Files to create**:
- `tech_writer/index/queries/javascript.scm`
- `tech_writer/index/queries/typescript.scm`
- `tech_writer/index/queries/go.scm`
- `tech_writer/index/queries/rust.scm`
- `tech_writer/index/queries/ruby.scm`
- `tech_writer/index/queries/java.scm`
- `tech_writer/index/queries/php.scm`
- `tech_writer/index/queries/cpp.scm`

See: `docs/designs/4/tech-design.md` §4.3 JavaScript/TypeScript Queries

**Tests**:
- Each language parses function definitions
- Each language parses class/struct definitions
- Each language parses imports

---

### 4-5: Implement IndexBuilder

Implement the IndexBuilder class for full and incremental indexing.

**Files to create**:
- `tech_writer/index/builder.py`

See: `docs/designs/4/tech-design.md` §3.1.2 Builder Interface

**Tests**:
- `_detect_language()` identifies all supported extensions
- `_compute_hash()` is deterministic
- `_discover_files()` excludes skip directories
- `build_full()` populates all tables
- `update_file()` detects changes via hash
- `remove_file()` cascades deletes

---

### 4-6: Implement QueryEngine

Implement the QueryEngine class for searching the index.

**Files to create**:
- `tech_writer/index/search.py`

See: `docs/designs/4/tech-design.md` §3.2.1 Search Interface

**Tests**:
- `expand_query()` extracts CamelCase
- `expand_query()` extracts snake_case
- `expand_query()` extracts backtick code
- `search_symbols()` returns scored results
- `search_symbols()` filters by kind
- `search_content()` uses FTS5
- `find_definition()` returns exact match
- `find_importers()` finds dependent files

---

### 4-7: Add unit tests for index module

Create comprehensive unit test suite for all index components.

**Files to create**:
- `tests/tech_writer/index/__init__.py`
- `tests/tech_writer/index/test_builder.py`
- `tests/tech_writer/index/test_parser.py`
- `tests/tech_writer/index/test_search.py`
- `tests/tech_writer/index/test_schema.py`

See: `docs/designs/4/tech-design.md` §6.1 Unit Tests

**Tests**: All unit tests pass

---

### 4-8: Implement SessionStart hook

Implement hook to initialize index and start file watcher on session start.

**Files to create**:
- `tech_writer/hooks/__init__.py`
- `tech_writer/hooks/common.py`
- `tech_writer/hooks/session_start.py`

See: `docs/designs/4/tech-design.md` §3.3.3 SessionStart Hook

**Tests**:
- Creates index if not exists
- Loads existing index
- Starts file watcher
- Writes PID file
- Handles missing project directory

---

### 4-9: Implement UserPromptSubmit hook

Implement hook to inject relevant code context into user prompts.

**Files to create**:
- `tech_writer/hooks/user_prompt_submit.py`

See: `docs/designs/4/tech-design.md` §3.3.4 UserPromptSubmit Hook

**Tests**:
- Extracts search terms from prompt
- Injects context for matching symbols
- Returns empty when no matches
- Respects MAX_CONTEXT_CHARS limit
- Handles missing index gracefully

---

### 4-10: Implement PostToolUse hook

Implement hook to update index when files are modified.

**Files to create**:
- `tech_writer/hooks/post_tool_use.py`

See: `docs/designs/4/tech-design.md` §3.3.5 PostToolUse Hook

**Tests**:
- Updates index on Write tool
- Updates index on Edit tool
- Ignores non-file-modifying tools
- Handles file deletion
- Handles missing index gracefully

---

### 4-11: Implement file watcher

Implement background file watcher for external changes.

**Files to create**:
- `tech_writer/index/watcher.py`

See: `docs/designs/4/tech-design.md` §3.4 File Watcher

**Tests**:
- Detects file modifications
- Detects file creation
- Detects file deletion
- Debounces rapid changes
- Skips excluded directories
- Can be started/stopped cleanly

---

### 4-12: Implement SessionEnd hook

Implement hook to cleanup file watcher on session end.

**Files to create**:
- `tech_writer/hooks/session_end.py`

See: `docs/designs/4/tech-design.md` §3.3 Hook Scripts

**Tests**:
- Stops file watcher by PID
- Removes PID file
- Handles missing PID file gracefully

---

### 4-13: Add integration tests

Create integration tests for the complete hook workflow.

**Files to create**:
- `tests/tech_writer/index/test_integration.py`
- `tests/tech_writer/hooks/test_hooks_integration.py`

See: `docs/designs/4/tech-design.md` §6.2 Integration Tests

**Tests**:
- Full index build on sample project
- Incremental update workflow
- Import tracking across files
- Hook stdin/stdout protocol compliance

---

### 4-14: Add BDD feature tests

Create BDD-style tests covering user scenarios.

**Files to create**:
- `tests/features/test_prompt_enrichment_bdd.py`

See: `docs/designs/4/tech-design.md` §6.3 BDD Feature Tests

**Tests**:
- Symbol injection on query
- No injection when no matches
- Index updates on file write
- Session lifecycle (start → work → end)

---

### 4-15: Create installation script and documentation

Create installation script and usage documentation.

**Files to create**:
- `scripts/install_hooks.sh`
- `docs/guides/prompt-enrichment.md`

See: `docs/designs/4/tech-design.md` §7 Configuration

**Deliverables**:
- Installation script works on macOS/Linux
- README updated with feature description
- Usage guide with examples
