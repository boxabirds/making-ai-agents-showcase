# Research: Live Codebase Sync with Claude Hooks

## Executive Summary

This research explores using Claude Code's hook system to maintain a persistent SQLite index that stays synchronized with codebase changes. The goal: accelerate "ask a question about the codebase" workflows by pre-indexing rather than relying on expensive tool-call discovery.

**Key Finding**: The hook system is event-driven on Claude-initiated actions, not a true file watcher. For bidirectional live sync, we need parallel file monitoring (fswatch/inotify) triggered at `SessionStart`, combined with `PostToolUse` hooks for Claude-side changes.

---

## 1. Claude Code Hook System Catalog

### 1.1 Available Hooks

| Hook Event | Trigger | Supports Matcher | Key Use Cases |
|-----------|---------|-----------------|---------------|
| `SessionStart` | Session begins | No | Initialize file watchers, load cached index |
| `SessionEnd` | Session ends | No | Persist index to disk, cleanup |
| `PreToolUse` | Before tool execution | Yes (tool name) | Block dangerous ops, modify tool input |
| `PostToolUse` | After tool completes | Yes (tool name) | Detect file changes, update index |
| `UserPromptSubmit` | User sends message | No | Inject cached context into prompts |
| `PermissionRequest` | Permission check | Yes | Auto-allow index operations |
| `Stop` | Agent tries to stop | No | Ensure index is saved |
| `SubagentStop` | Subagent stops | No | Coordinate multi-agent index access |
| `Notification` | System alert | Yes | Handle index errors |
| `PreCompact` | Before token compaction | No | Summarize index state before context loss |

### 1.2 Hook Configuration Format

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python /path/to/init_index.py",
        "timeout": 30
      }]
    }],
    "PostToolUse": [{
      "matcher": "Write|Edit|Bash",
      "hooks": [{
        "type": "command",
        "command": "python /path/to/update_index.py"
      }]
    }],
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python /path/to/inject_context.py"
      }]
    }]
  }
}
```

### 1.3 Data Flow to Hooks

All hooks receive JSON via stdin:

```json
{
  "session_id": "unique-session-id",
  "hook_event_name": "PostToolUse",
  "transcript_path": "/path/to/transcript.md",
  "tool_name": "Write",
  "tool_input": {"path": "src/main.py", "content": "..."},
  "tool_output": "File written successfully"
}
```

### 1.4 Hook Response Semantics

| Exit Code | Meaning | Behavior |
|-----------|---------|----------|
| 0 | Success | Stdout can contain JSON response |
| 1 | Non-blocking error | Stderr shown, execution continues |
| 2 | Blocking error | Action prevented |

**UserPromptSubmit response (critical for context injection)**:
```json
{
  "additionalContext": "## Pre-loaded Index Context\n\nSymbols found: 847\nFiles indexed: 234\n..."
}
```

---

## 2. Where Are the Real Overheads?

### 2.1 Current Workflow Analysis

The current tech_writer pipeline has these phases:

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Exploration (100-800 LLM tool calls)                   │
│ - list_files() → discover structure                             │
│ - get_structure() → parse symbols (tree-sitter)                 │
│ - read_file() → load content into cache                         │
│ - get_imports(), get_references() → semantic queries            │
└─────────────────────────────────────────────────────────────────┘
                              │
                    LLM decides next tool
                              │
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2-4: Generate outline, sections, assemble                 │
│ - search_text() → FTS5 queries on cached content                │
│ - read_file() → retrieve from cache                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Overhead Breakdown

| Operation | Typical Time | Bottleneck? |
|-----------|-------------|-------------|
| **LLM inference** | 1-5s per call | **YES** - dominates wall time |
| File system read | 1-10ms | No |
| Tree-sitter parse | 10-100ms | Marginal |
| SQLite insert | <1ms | No |
| FTS5 search | 1-5ms | No |
| Tool call overhead | ~100ms | Marginal |

**Key Insight**: LLM inference is 100-1000x slower than any local operation. The bottleneck is **how many LLM calls** are needed, not the tool execution time.

### 2.3 Why Tool Calling is Expensive

Consider "Where is the database connection handled?":

**Without Index (Current Agent Approach)**:
```
1. LLM: "I should list files" → list_files() → 50ms
2. LLM: "Let me check src/" → list_files(src/) → 50ms
3. LLM: "database.py looks relevant" → read_file() → 10ms
4. LLM: "This is config, let me search" → grep("connection") → 100ms
5. ... repeat 10-50 times ...

Total: 10-50 LLM calls × 2-5s = 20-250 seconds
```

**With Pre-built Index**:
```
1. Query index: WHERE name LIKE '%connection%' AND kind='function' → 5ms
2. Return: [{file: "src/db.py", line: 45, name: "get_connection"}]
3. Single LLM call to synthesize answer

Total: 1-3 LLM calls × 2-5s = 2-15 seconds
```

---

## 3. Index-Accelerated Architecture

### 3.1 What to Index

```sql
-- Current tech_writer schema (already implemented)
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    content TEXT,
    lang TEXT,
    line_count INTEGER,
    hash TEXT,         -- For change detection
    cached_at TEXT
);

CREATE TABLE symbols (
    file_id INTEGER,
    name TEXT,
    kind TEXT,         -- function, class, method, variable
    line INTEGER,
    end_line INTEGER,
    signature TEXT,
    doc TEXT
);

CREATE VIRTUAL TABLE files_fts USING fts5(path, content);

-- NEW: Additional indexes for accelerated queries
CREATE TABLE imports (
    file_id INTEGER,
    imported_name TEXT,
    imported_from TEXT,
    line INTEGER
);

CREATE TABLE references (
    symbol_id INTEGER,
    referencing_file_id INTEGER,
    line INTEGER
);

CREATE INDEX idx_symbols_kind ON symbols(kind);
CREATE INDEX idx_imports_name ON imports(imported_name);
```

### 3.2 Pre-computed Queries

| Query Pattern | Without Index | With Index |
|---------------|---------------|------------|
| "Find function X" | grep + LLM reasoning (5-10 calls) | `SELECT * FROM symbols WHERE name = 'X'` |
| "What imports Y?" | grep + read files (10-20 calls) | `SELECT f.path FROM imports i JOIN files f...` |
| "Show class structure" | get_structure per file (N calls) | `SELECT * FROM symbols WHERE kind='class'` |
| "Search for pattern" | grep + filter (variable) | FTS5 `MATCH` query |

### 3.3 Hook Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Code Session                          │
└─────────────────────────────────────────────────────────────────┘
        │                    │                       │
        ▼                    ▼                       ▼
   SessionStart         PostToolUse            UserPromptSubmit
        │                    │                       │
        ▼                    ▼                       ▼
┌───────────────┐   ┌───────────────┐      ┌───────────────┐
│ Load Index    │   │ Detect Change │      │ Inject Index  │
│ Start Watcher │   │ Update Index  │      │ Context       │
└───────────────┘   └───────────────┘      └───────────────┘
        │                    │                       │
        └────────────────────┴───────────────────────┘
                             │
                             ▼
                    ┌───────────────┐
                    │ SQLite Index  │
                    │ .tech_writer/ │
                    │   index.db    │
                    └───────────────┘
```

---

## 4. Use Case: "Ask a Question of the Codebase"

### 4.1 Current Approach (Typical Coding Agents)

```
User: "How does authentication work in this codebase?"

Agent thinking:
1. grep for "auth" → 50 results
2. grep for "login" → 30 results
3. Read each promising file → 10-20 read_file calls
4. Analyze relationships → more greps and reads
5. Synthesize answer

Result: 30-100 tool calls, 60-500 seconds
```

### 4.2 Index-Accelerated Approach

```
User: "How does authentication work in this codebase?"

Hook (UserPromptSubmit) injects context:
"""
## Codebase Index Summary
- 234 files, 847 symbols indexed
- Auth-related symbols found:
  - class AuthMiddleware [src/auth/middleware.py:15-89]
  - function verify_token [src/auth/jwt.py:23-45]
  - function login_user [src/auth/views.py:12-34]
  - function hash_password [src/auth/utils.py:5-15]
- Import graph: middleware imports jwt, views imports utils
"""

Agent thinking:
1. I have the relevant locations pre-indexed
2. Read AuthMiddleware implementation → 1 read_file
3. Read verify_token → 1 read_file
4. Synthesize answer with citations

Result: 3-5 tool calls, 10-25 seconds
```

### 4.3 Context Injection Strategy

The `UserPromptSubmit` hook is the key accelerator:

```python
#!/usr/bin/env python3
"""UserPromptSubmit hook: inject relevant index context."""

import json
import sqlite3
import sys

def main():
    input_data = json.load(sys.stdin)
    user_prompt = input_data.get("user_prompt", "")

    # Extract likely search terms from prompt
    keywords = extract_keywords(user_prompt)

    # Query index
    conn = sqlite3.connect(".tech_writer/index.db")

    # Find relevant symbols
    relevant_symbols = []
    for kw in keywords:
        cursor = conn.execute("""
            SELECT s.name, s.kind, f.path, s.line, s.end_line, s.doc
            FROM symbols s JOIN files f ON s.file_id = f.id
            WHERE s.name LIKE ? OR s.doc LIKE ?
            LIMIT 10
        """, (f"%{kw}%", f"%{kw}%"))
        relevant_symbols.extend(cursor.fetchall())

    # Format context
    if relevant_symbols:
        context = "## Pre-indexed Relevant Code\n\n"
        for sym in relevant_symbols[:15]:
            name, kind, path, line, end_line, doc = sym
            context += f"- {kind} `{name}` [{path}:{line}-{end_line}]\n"
            if doc:
                context += f"  {doc[:100]}...\n"

        print(json.dumps({"additionalContext": context}))

    sys.exit(0)

def extract_keywords(prompt):
    """Extract likely code-relevant keywords from natural language prompt."""
    # Simple heuristic: CamelCase, snake_case, quoted terms
    import re
    keywords = []
    keywords.extend(re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+', prompt))  # CamelCase
    keywords.extend(re.findall(r'[a-z]+_[a-z_]+', prompt))  # snake_case
    keywords.extend(re.findall(r'"([^"]+)"', prompt))  # Quoted
    keywords.extend(re.findall(r'`([^`]+)`', prompt))  # Backtick
    return list(set(keywords))

if __name__ == "__main__":
    main()
```

---

## 5. Live Sync Strategy

### 5.1 The Bidirectional Problem

Changes come from two directions:

| Source | Detection Method | Update Trigger |
|--------|------------------|----------------|
| **Claude edits** | `PostToolUse` on Write/Edit/Bash | Hook fires automatically |
| **External edits** | File system watcher | Background process needed |

### 5.2 SessionStart: Initialize Watcher

```python
#!/usr/bin/env python3
"""SessionStart hook: load index, start file watcher."""

import json
import os
import subprocess
import sys
from pathlib import Path

INDEX_PATH = ".tech_writer/index.db"
WATCHER_PID_FILE = ".tech_writer/watcher.pid"

def main():
    input_data = json.load(sys.stdin)
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    # Initialize index if missing
    index_path = Path(project_dir) / INDEX_PATH
    if not index_path.exists():
        print(f"Index not found at {index_path}, will build on first query",
              file=sys.stderr)
    else:
        # Validate index integrity
        import sqlite3
        conn = sqlite3.connect(str(index_path))
        try:
            count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            print(f"Index loaded: {count} files cached", file=sys.stderr)
        except sqlite3.Error as e:
            print(f"Index corrupted, will rebuild: {e}", file=sys.stderr)
        finally:
            conn.close()

    # Start file watcher (background process)
    watcher_script = Path(project_dir) / ".tech_writer/file_watcher.py"
    if watcher_script.exists():
        proc = subprocess.Popen(
            [sys.executable, str(watcher_script), project_dir],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Save PID for cleanup
        pid_file = Path(project_dir) / WATCHER_PID_FILE
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(proc.pid))
        print(f"File watcher started (PID {proc.pid})", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### 5.3 PostToolUse: Incremental Index Update

```python
#!/usr/bin/env python3
"""PostToolUse hook: update index on file modifications."""

import json
import sqlite3
import sys
from pathlib import Path

def main():
    input_data = json.load(sys.stdin)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only handle file-modifying tools
    if tool_name not in ("Write", "Edit", "Bash"):
        sys.exit(0)

    # Extract modified file path
    file_path = None
    if tool_name in ("Write", "Edit"):
        file_path = tool_input.get("path") or tool_input.get("file_path")
    elif tool_name == "Bash":
        # Parse command for file modifications (heuristic)
        cmd = tool_input.get("command", "")
        # Skip if not a file-modifying command
        if not any(op in cmd for op in [">", "mv ", "cp ", "touch ", "rm "]):
            sys.exit(0)

    if file_path:
        update_index_for_file(file_path)

    sys.exit(0)

def update_index_for_file(file_path: str):
    """Re-index a single file."""
    import hashlib
    from datetime import datetime

    path = Path(file_path)
    if not path.exists():
        # File deleted - remove from index
        remove_from_index(file_path)
        return

    # Read and hash content
    try:
        content = path.read_text()
    except Exception:
        return

    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    conn = sqlite3.connect(".tech_writer/index.db")

    # Check if file changed
    cursor = conn.execute(
        "SELECT hash FROM files WHERE path = ?", (file_path,)
    )
    existing = cursor.fetchone()

    if existing and existing[0] == content_hash:
        # No change
        conn.close()
        return

    # Update or insert file
    line_count = content.count('\n') + 1
    lang = detect_language(file_path)
    cached_at = datetime.utcnow().isoformat()

    if existing:
        conn.execute("""
            UPDATE files SET content=?, lang=?, line_count=?, hash=?, cached_at=?
            WHERE path=?
        """, (content, lang, line_count, content_hash, cached_at, file_path))
        file_id = conn.execute(
            "SELECT id FROM files WHERE path=?", (file_path,)
        ).fetchone()[0]
    else:
        cursor = conn.execute("""
            INSERT INTO files (path, content, lang, line_count, hash, cached_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_path, content, lang, line_count, content_hash, cached_at))
        file_id = cursor.lastrowid

    # Re-parse symbols
    symbols = parse_symbols(content, lang)
    conn.execute("DELETE FROM symbols WHERE file_id=?", (file_id,))
    for sym in symbols:
        conn.execute("""
            INSERT INTO symbols (file_id, name, kind, line, end_line, signature, doc)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (file_id, sym['name'], sym['kind'], sym['line'],
              sym.get('end_line'), sym.get('signature'), sym.get('doc')))

    conn.commit()
    conn.close()
    print(f"Index updated: {file_path}", file=sys.stderr)

def remove_from_index(file_path: str):
    """Remove a deleted file from index."""
    conn = sqlite3.connect(".tech_writer/index.db")
    cursor = conn.execute("SELECT id FROM files WHERE path=?", (file_path,))
    row = cursor.fetchone()
    if row:
        file_id = row[0]
        conn.execute("DELETE FROM symbols WHERE file_id=?", (file_id,))
        conn.execute("DELETE FROM files WHERE id=?", (file_id,))
        conn.commit()
        print(f"Index removed: {file_path}", file=sys.stderr)
    conn.close()

def detect_language(path: str) -> str:
    ext_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.rs': 'rust', '.go': 'go', '.java': 'java', '.rb': 'ruby',
        '.c': 'c', '.cpp': 'cpp', '.h': 'c', '.hpp': 'cpp',
    }
    return ext_map.get(Path(path).suffix.lower(), 'unknown')

def parse_symbols(content: str, lang: str) -> list:
    """Parse symbols from content using tree-sitter."""
    # Simplified - real implementation would use tree-sitter
    # See tech_writer/tools/semantic.py for full implementation
    return []

if __name__ == "__main__":
    main()
```

### 5.4 External File Watcher

```python
#!/usr/bin/env python3
"""Background file watcher for external edits."""

import hashlib
import sqlite3
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class IndexUpdateHandler(FileSystemEventHandler):
    def __init__(self, index_path: str, project_root: Path):
        self.index_path = index_path
        self.project_root = project_root
        self.debounce = {}  # path -> last_update_time

    def on_modified(self, event):
        if event.is_directory:
            return
        self._handle_change(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle_change(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        self._handle_deletion(event.src_path)

    def _handle_change(self, abs_path: str):
        # Debounce rapid changes
        now = time.time()
        if abs_path in self.debounce:
            if now - self.debounce[abs_path] < 0.5:
                return
        self.debounce[abs_path] = now

        # Get relative path
        try:
            rel_path = Path(abs_path).relative_to(self.project_root)
        except ValueError:
            return

        # Skip non-source files
        if not self._is_source_file(rel_path):
            return

        # Update index (same logic as PostToolUse hook)
        update_index_for_file(str(rel_path), self.index_path)

    def _handle_deletion(self, abs_path: str):
        try:
            rel_path = Path(abs_path).relative_to(self.project_root)
        except ValueError:
            return
        remove_from_index(str(rel_path), self.index_path)

    def _is_source_file(self, path: Path) -> bool:
        SOURCE_EXTENSIONS = {'.py', '.js', '.ts', '.rs', '.go', '.java', '.rb'}
        return path.suffix.lower() in SOURCE_EXTENSIONS

def main():
    if len(sys.argv) < 2:
        print("Usage: file_watcher.py <project_root>", file=sys.stderr)
        sys.exit(1)

    project_root = Path(sys.argv[1])
    index_path = project_root / ".tech_writer" / "index.db"

    handler = IndexUpdateHandler(str(index_path), project_root)
    observer = Observer()
    observer.schedule(handler, str(project_root), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
```

---

## 6. Overhead Analysis: Index vs No Index

### 6.1 Benchmark Scenarios

| Scenario | Without Index | With Index | Speedup |
|----------|---------------|------------|---------|
| "Find function foo" | 5-10 LLM calls (10-50s) | 1 SQL + 1-2 LLM (3-10s) | **3-5x** |
| "How does auth work?" | 30-50 LLM calls (60-250s) | 3-5 LLM calls (10-25s) | **5-10x** |
| "List all endpoints" | 20-30 LLM calls (40-150s) | 1 SQL + 1 LLM (3-8s) | **10-20x** |
| "Full documentation" | 100-500 LLM calls (5-30min) | 50-200 LLM calls (3-15min) | **1.5-2x** |

### 6.2 Where Index Helps Most

1. **Symbol lookup**: Direct SQL vs iterative grep + LLM reasoning
2. **Cross-reference queries**: Pre-computed import/reference graphs
3. **Structural questions**: Pre-parsed AST data vs repeated parsing
4. **Context injection**: Relevant code surfaced before LLM even starts

### 6.3 Where Index Helps Least

1. **Deep code understanding**: LLM still needs to read and reason
2. **Novel patterns**: Index can't predict what's relevant
3. **First-time indexing**: Upfront cost to build index (~1-5s per 100 files)

---

## 7. Implementation Roadmap

### Phase 1: Persistent Index (Low Effort)
- [x] SQLite cache already exists (`tech_writer/store.py`)
- [ ] Add `--persist-index` flag to save cache between runs
- [ ] Add hash-based change detection (already has `hash` column)

### Phase 2: Hook Integration (Medium Effort)
- [ ] Create `.claude/settings.json` with hook configuration
- [ ] Implement `SessionStart` hook for index loading
- [ ] Implement `PostToolUse` hook for incremental updates
- [ ] Test with Claude Code CLI

### Phase 3: Context Injection (Medium Effort)
- [ ] Implement `UserPromptSubmit` hook for relevance matching
- [ ] Add keyword extraction from natural language
- [ ] Format and inject relevant index context
- [ ] Tune context size to avoid overwhelming LLM

### Phase 4: External Sync (Higher Effort)
- [ ] Add watchdog-based file watcher
- [ ] Handle concurrent index access (SQLite locking)
- [ ] Add `SessionEnd` hook for cleanup
- [ ] Test bidirectional sync scenarios

### Phase 5: Query Acceleration (Highest Impact)
- [ ] Add import/reference graph to index
- [ ] Pre-compute common query patterns
- [ ] Add semantic similarity search (embeddings?)
- [ ] Expose index queries as direct tools

---

## 8. Limitations and Trade-offs

### 8.1 Hook System Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Event-driven only | Can't detect external edits | Parallel file watcher |
| 60s timeout | Complex sync may fail | Spawn background process |
| No guaranteed ordering | Multi-file ops may race | Debounce + atomic updates |
| Bash execution security | Hooks run with user privileges | Sandboxed index operations |

### 8.2 Index Freshness Trade-offs

| Strategy | Freshness | Overhead | Complexity |
|----------|-----------|----------|------------|
| On-demand (current) | Always fresh | High per-query | Low |
| Session-start build | Fresh at start | Medium upfront | Low |
| Live sync (hooks) | Near-real-time | Low ongoing | Medium |
| Full live (watcher) | Real-time | Very low | High |

### 8.3 Honest Assessment

**The hook system alone won't solve the problem**. Here's why:

1. **LLM is still the bottleneck**: Even with perfect indexing, the LLM must still reason about code. Index reduces tool calls but not thinking time.

2. **Context window limits**: Can't inject entire index into prompt. Must do relevance filtering, which itself requires intelligence.

3. **Semantic understanding**: Index captures syntax (symbols, imports). Understanding "how auth works" requires semantic reasoning the index can't provide.

**Where it WILL help**: Reducing the discovery phase. Instead of 50 grep+read cycles to find relevant code, inject the top 10 relevant files/symbols directly. That's a real 5-10x speedup on specific query types.

---

## 9. Case Study: Zed Editor's Approach

### 9.1 What Zed Does Well

Zed (github.com/zed-industries/zed) is a Rust-based IDE from the creators of Tree-sitter. Their architecture offers lessons for our indexing approach:

**File System Watching** ([worktree.rs](https://github.com/zed-industries/zed/blob/main/crates/worktree/src/worktree.rs)):
- Uses `FS_WATCH_LATENCY = 100ms` debouncing for rapid changes
- Tracks files by **inode** (not just path) to detect renames/moves
- `scan_id` versioning for coordinating parallel operations without blocking
- Differential updates via `UpdatedEntriesSet` - only transmit changes, not full snapshots
- Gitignore parsing cached in `ignores_by_parent_abs_path` with staleness flags

**Symbol Extraction** ([outline.rs](https://github.com/zed-industries/zed/blob/main/crates/outline/src/outline.rs)):
- Tree-sitter queries with semantic captures: `@context`, `@name`, `@item`
- Language-specific query patterns (e.g., Rust structs, functions, fields)
- No hardcoded extraction logic - fully query-driven

**Project-Wide Symbol Search** ([project_symbols.rs](https://github.com/zed-industries/zed/blob/main/crates/project_symbols/src/project_symbols.rs)):
- Collects symbols via **LSP** (Language Server Protocol), not custom parsing
- Separates `visible_match_candidates` (project) from `external_match_candidates` (libraries)
- Fuzzy matching with `fuzzy::match_strings`, capped at 100 results
- Sorting: `Reverse(OrderedFloat(score))` with alphabetical tiebreaker

**Search** ([project_search.rs](https://github.com/zed-industries/zed/blob/main/crates/search/src/project_search.rs)):
- Async streaming: results arrive in 1024-match batches
- MultiBuffer excerpts with configurable context lines
- Document order (as encountered), not relevance-ranked

### 9.2 What Zed Tried and Abandoned

**Semantic Index with Embeddings** - Zed built and then **removed** this feature:

> "We are temporarily removing the semantic index in order to redesign it from scratch."
> — [Zed v0.128.3 Release Notes](https://zed.dev/releases/stable/0.128.3)

**Why it failed** (from [Nathan's discussion](https://github.com/zed-industries/zed/discussions/9442)):

1. **OpenAI embeddings weren't designed for code** - built for prose, not syntax
2. **Quality was too low** - search results weren't good enough to be useful
3. **Friction was too high** - the workflow didn't feel natural
4. **Token cost issues** - initially batched by span count, had to switch to token-based batching

**Optimizations they tried before giving up**:
- Embeddings cache to avoid re-embedding on every save
- Token-based batching (reduced API calls)
- 75% reduction in incremental indexing token usage

**Current state**: Users [are asking](https://github.com/zed-industries/zed/issues/15924) for embedding context to return, citing Cursor's full codebase indexing as a competitive advantage. Zed team hasn't publicly committed to a timeline.

### 9.3 Lessons for Our Approach

| Zed Learning | Implication for tech_writer |
|--------------|----------------------------|
| LSP for symbols | Consider LSP integration over custom parsing for mature languages |
| Inode tracking | Hash-based change detection (we already have this) is sufficient for our use case |
| Embeddings were low quality | Don't assume embeddings will solve semantic search - test quality first |
| Friction matters | Context injection must be seamless, not require user action |
| OpenAI embeddings ≠ code | If using embeddings, evaluate code-specific models (CodeBERT, StarCoder embeddings) |
| Users still want it | Despite failure, the feature is highly requested - worth solving |

### 9.4 Key Architectural Differences

| Aspect | Zed | tech_writer |
|--------|-----|-------------|
| Primary use | Real-time editing | Batch documentation |
| Symbol source | LSP servers | Tree-sitter direct |
| Index persistence | In-memory (session) | SQLite (cross-session) |
| Query interface | Fuzzy picker UI | LLM prompt injection |
| Change detection | Inode + mtime | Content hash |
| Embedding approach | Removed (failed) | Not yet attempted |

**Our advantage**: We're not real-time. We can afford 200ms for LLM query expansion where Zed needs sub-10ms picker responsiveness. This opens approaches Zed couldn't use.

---

## 10. Conclusions

### 10.1 Recommended Approach

1. **Start with `UserPromptSubmit` hook**: Highest impact, lowest complexity. Inject pre-indexed context at query time.

2. **Add `PostToolUse` for incremental updates**: Keep index fresh as Claude makes changes.

3. **Consider file watcher only if needed**: External edit sync adds complexity. May not be worth it if most edits happen through Claude.

4. **Don't over-index**: Symbols + FTS is sufficient. Complex graphs (call graph, data flow) have diminishing returns vs implementation cost.

### 10.2 Expected Outcomes

| Use Case | Current | With Index | Improvement |
|----------|---------|------------|-------------|
| Quick code question | 30-60s | 5-15s | **4-6x faster** |
| Find specific function | 10-30s | 2-5s | **5-6x faster** |
| Full documentation run | 5-30min | 3-20min | **1.5x faster** |
| Repeated queries (same session) | Same | Much faster | **Index cached** |

### 10.3 Next Steps

1. Prototype `UserPromptSubmit` hook with current SQLite schema
2. Benchmark on real "ask a question" scenarios
3. Measure LLM call reduction vs wall-clock improvement
4. Iterate on relevance algorithm for context injection
