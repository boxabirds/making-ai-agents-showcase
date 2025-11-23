# Infinite-Scalability Tech Writer Agent

## Goals
- Handle arbitrary-size codebases without context overruns.
- Produce arbitrary-length, citation-backed reports.
- Be agentic: LLM decides what to explore via semantic tools.
- Cost scales with query complexity, not repo size.

## Design Principles

1. **Agentic exploration.** LLM decides what files to read via tool calls.
2. **Semantic tools.** Tree-sitter powers structured queries ("what functions exist?") instead of regex grep.
3. **Lazy caching.** Only cache files the LLM actually reads.
4. **Section-by-section output.** Generate outline, then each section separately. Arbitrary length.
5. **Citation grounding.** Every claim must cite content the LLM actually read.

## Architecture Overview

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 1: EXPLORATION (agentic)                         │
│                                                         │
│  LLM has semantic tools:                                │
│    - list_files(pattern) → file paths                   │
│    - read_file(path) → content (parsed + cached)        │
│    - get_symbols(path) → functions/classes              │
│    - get_imports(path) → dependencies                   │
│    - get_definition(name) → where is X defined?         │
│    - get_references(name) → where is X used?            │
│                                                         │
│  LLM explores until it understands enough to outline.   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 2: OUTLINE (1 LLM call)                          │
│                                                         │
│  Generate report structure:                             │
│    ["Introduction", "Authentication", "API", ...]       │
│                                                         │
│  Each section has a focus and relevant files.           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 3: SECTION GENERATION (agentic, per section)     │
│                                                         │
│  For each section:                                      │
│    - LLM can do more exploration if needed              │
│    - Generate section content with citations            │
│    - Citations must reference cached content            │
│                                                         │
│  Output: N sections, each with inline citations         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 4: ASSEMBLY & VERIFICATION                       │
│                                                         │
│  - Combine sections into final report                   │
│  - Verify all citations resolve to cached content       │
│  - Flag any invalid citations                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
              Final Report
```

## Phase 1: Exploration Tools

The LLM drives exploration. Tools answer **semantic questions**, not regex queries.

Tree-sitter parses files on read, enabling structured queries. The LLM asks "what functions exist?" not "grep for def".

### File System Tools

#### `list_files`

```python
def list_files(pattern: str = "*", path: str = ".") -> list[str]:
    """
    List files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "*.py", "src/**/*.ts")
        path: Directory to search in

    Returns:
        List of file paths relative to repo root
    """
```

#### `read_file`

```python
def read_file(path: str, start_line: int = None, end_line: int = None) -> str:
    """
    Read a file's contents.

    Side effects:
        - Parses with tree-sitter (if supported language)
        - Caches content + symbols
        - Enables semantic queries on this file

    Returns:
        File content (or line range).
    """
```

### Semantic Tools (tree-sitter powered)

These tools give complete answers. No grep thrashing.

#### `get_symbols`

```python
def get_symbols(path: str, kind: str = None) -> list[dict]:
    """
    Get all symbols defined in a file.

    Args:
        path: File path (reads file if not already cached)
        kind: Optional filter: "function", "class", "method", "variable"

    Returns:
        [{"name": "authenticate", "kind": "function", "line": 45, "end_line": 67,
          "signature": "def authenticate(user, password)", "doc": "..."},
         ...]

    Complete list. No guessing. No repeated searches.
    """
```

#### `get_imports`

```python
def get_imports(path: str) -> list[dict]:
    """
    Get all imports/dependencies in a file.

    Returns:
        [{"module": "flask", "names": ["Flask", "request"], "line": 1},
         {"module": "./auth", "names": ["validate"], "line": 3},
         ...]

    Know immediately what a file depends on.
    """
```

#### `get_definition`

```python
def get_definition(name: str) -> dict | None:
    """
    Find where a symbol is defined (across all read files).

    Args:
        name: Symbol name (function, class, variable)

    Returns:
        {"path": "src/auth.py", "line": 45, "kind": "function", "signature": "..."}
        or None if not found in read files.

    One call. Exact location.
    """
```

#### `get_references`

```python
def get_references(name: str) -> list[dict]:
    """
    Find all usages of a symbol (across all read files).

    Returns:
        [{"path": "src/api.py", "line": 23, "context": "result = authenticate(...)"},
         ...]

    Answers "where is this used?" without grep.
    """
```

#### `get_structure`

```python
def get_structure(path: str) -> dict:
    """
    Get the structural overview of a file.

    Returns:
        {
            "classes": [
                {"name": "AuthManager", "line": 10, "methods": ["login", "logout", "refresh"]},
            ],
            "functions": [
                {"name": "validate_token", "line": 89},
            ],
            "exports": ["AuthManager", "validate_token"]
        }

    Understand file organization in one call.
    """
```

### Text Search (fallback)

#### `search_text`

```python
def search_text(query: str, file_pattern: str = None) -> list[dict]:
    """
    Full-text search across cached files. Use semantic tools first;
    this is for finding strings, comments, or unsupported languages.

    Returns:
        [{"path": str, "line": int, "content": str}, ...]
    """
```

### Control Flow

#### `finish_exploration`

```python
def finish_exploration(understanding: str) -> None:
    """
    Signal that exploration is complete. Triggers outline generation.

    Args:
        understanding: Brief summary of what was learned
    """
```

## Why Semantic Tools Matter

| LLM question | Regex approach | Semantic approach |
|--------------|----------------|-------------------|
| "What functions are in auth.py?" | `grep "def "` (misses methods, lambdas) | `get_symbols("auth.py", kind="function")` → complete list |
| "What does this file import?" | `grep "import\|from"` (parsing hell) | `get_imports("auth.py")` → structured data |
| "Where is User defined?" | `grep "class User"` across files | `get_definition("User")` → exact location |
| "What calls authenticate()?" | `grep "authenticate("` (false positives) | `get_references("authenticate")` → actual call sites |

The LLM asks once, gets a complete answer, moves on.

## Phase 2: Outline Generation

After exploration, one LLM call generates the report structure.

**Prompt:**
```
Based on your exploration of the codebase, create an outline for the report.

User's request: {prompt}

Files you explored: {cached_files}

Your understanding: {exploration_summary}

Output a JSON array of sections:
[
  {"title": "Introduction", "focus": "Overview of the system", "relevant_files": ["README.md", "src/main.py"]},
  {"title": "Authentication", "focus": "How auth works", "relevant_files": ["src/auth.py", "src/middleware.py"]},
  ...
]
```

## Phase 3: Section Generation

Each section is generated independently, allowing arbitrary total length.

**Section generation is itself agentic:**
- LLM sees the section focus and relevant files
- Can call `read_file` or semantic tools for more detail
- Eventually outputs section content with citations

**Prompt for section:**
```
Write the "{section.title}" section of the report.

Focus: {section.focus}

User's original request: {prompt}

Available evidence (from files you've read):
{cached_content_for_relevant_files}

Rules:
1. Every statement must cite evidence using [path:start-end] format
2. You can read additional files if needed using the read_file tool
3. Do not invent facts - only cite what you've read
4. When done, output the section content in markdown
```

## Phase 4: Assembly & Verification

Combine sections and verify citations.

- Join all sections into final markdown
- Extract all citations from the report
- Verify each citation resolves to cached content
- Flag invalid citations (file not read, or line range doesn't exist)

If invalid citations exist:
- Flag them in the output
- Re-generate affected sections with stricter instructions
- Or accept best-effort output

## Citation Format

Format: `path:start_line-end_line`

Examples:
- `src/auth.py:10-25`
- `lib/utils/helpers.ts:100-150`

Citations are verified against cached content. If the LLM cites a file it didn't read, that's invalid.

## Storage

SQLite caches what was read during the run:
- File content (for citation verification)
- Parsed symbols (for semantic queries)
- FTS index on cached content (for text search fallback)

The cache grows as the LLM explores. If the LLM only reads 10 files, only 10 files are cached.

Cache is per-run by default; optionally persisted for debugging.

## Example Flow

**Prompt:** "Write documentation for the API endpoints in this Flask app"

**Phase 1 - Exploration:**
```
LLM: list_files("*.py")
Tool: ["app.py", "routes/users.py", "routes/orders.py", "models.py", "config.py"]

LLM: read_file("app.py")
Tool: [content of app.py - Flask app initialization]

LLM: get_structure("app.py")
Tool: {"functions": [...], "imports": ["flask", "routes.users", "routes.orders"]}

LLM: read_file("routes/users.py")
Tool: [content - user CRUD endpoints]

LLM: get_symbols("routes/users.py", kind="function")
Tool: [{"name": "get_user", "line": 10}, {"name": "create_user", "line": 25}, ...]

LLM: read_file("routes/orders.py")
Tool: [content - order endpoints]

LLM: finish_exploration("Flask app with user and order REST endpoints")
```

**Phase 2 - Outline:**
```json
[
  {"title": "Overview", "focus": "API structure", "relevant_files": ["app.py"]},
  {"title": "User Endpoints", "focus": "/users routes", "relevant_files": ["routes/users.py"]},
  {"title": "Order Endpoints", "focus": "/orders routes", "relevant_files": ["routes/orders.py"]}
]
```

**Phase 3 - Sections:**
Each section generated with citations to the files that were read.

**Phase 4 - Assembly:**
Combine sections, verify citations, output final report.

## CLI

```bash
# Basic usage
python -m tech_writer --prompt prompt.md --repo /path/to/repo

# Remote repo
python -m tech_writer --prompt prompt.md --repo https://github.com/user/repo

# Control exploration depth
python -m tech_writer --prompt prompt.md --repo /path/to/repo --max-exploration 30

# Control output sections
python -m tech_writer --prompt prompt.md --repo /path/to/repo --max-sections 20

# Persist cache for debugging
python -m tech_writer --prompt prompt.md --repo /path/to/repo --persist-cache
```

## Testing Strategy

1. **Tool tests:** Each semantic tool returns correct results for known code
2. **Exploration tests:** LLM can find relevant files for known queries
3. **Citation tests:** Only cached content can be cited; invalid citations are caught
4. **Integration tests:** End-to-end on small fixture repos
