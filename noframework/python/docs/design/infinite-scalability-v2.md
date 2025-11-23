# Infinite-Scalability Tech Writer Agent v2

## Goals
- Handle arbitrary-size codebases without context overruns.
- Produce arbitrary-length, citation-backed reports.
- Be agentic: LLM decides what to explore, not brute-force ingest.
- Minimize LLM calls: O(sections) for output, exploration is query-driven.

## Design Principles

1. **Agentic exploration.** LLM decides what files to read via tool calls. No upfront "parse everything."
2. **Lazy indexing.** Only parse/index files the LLM actually reads. SQLite is a cache, not a pre-computed index.
3. **Section-by-section output.** Generate outline, then each section separately. Arbitrary length.
4. **Citation grounding.** Every claim must cite content the LLM actually read.

## Architecture Overview

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 1: EXPLORATION (agentic)                         │
│                                                         │
│  LLM has tools:                                         │
│    - list_files(pattern) → file paths                   │
│    - read_file(path) → content (cached + parsed)        │
│    - search_code(query) → matching chunks               │
│    - get_symbols(path) → functions/classes in file      │
│                                                         │
│  LLM explores until it understands enough to outline.   │
│  All reads are cached in SQLite for citation.           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 2: OUTLINE (1 LLM call)                          │
│                                                         │
│  Based on exploration, generate report outline:         │
│    ["Introduction", "Authentication", "API", ...]       │
│                                                         │
│  Each section has a focus query for retrieval.          │
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
│  - Verify all citations resolve to cached chunks        │
│  - Flag any invalid citations                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
              Final Report
```

**LLM calls:** O(exploration steps) + 1 (outline) + O(sections)

For a 10-section report with moderate exploration: ~15-25 LLM calls total.
Compared to v1's 1,100+ calls for summarization alone.

## Phase 1: Exploration Tools

The LLM drives exploration. Tools are the interface.

### Tool: `list_files`

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

### Tool: `read_file`

```python
def read_file(path: str, start_line: int = None, end_line: int = None) -> str:
    """
    Read a file's contents. Automatically parses and caches for citation.

    Args:
        path: File path relative to repo root
        start_line: Optional start line (1-indexed)
        end_line: Optional end line (inclusive)

    Returns:
        File content (or specified line range)

    Side effects:
        - Parses file with tree-sitter if supported language
        - Caches content in SQLite for citation verification
        - Extracts symbols for later reference
    """
```

### Tool: `search_code`

```python
def search_code(query: str, file_pattern: str = None) -> list[dict]:
    """
    Search for code matching a query across cached files.

    Args:
        query: Search string or regex
        file_pattern: Optional glob to filter files

    Returns:
        List of matches: [{"path": str, "line": int, "content": str}, ...]

    Note:
        Only searches files that have been read. If no results,
        LLM should read more files first.
    """
```

### Tool: `get_symbols`

```python
def get_symbols(path: str) -> list[dict]:
    """
    Get symbols (functions, classes, etc.) defined in a file.

    Args:
        path: File path (must have been read first)

    Returns:
        List of symbols: [{"name": str, "kind": str, "line": int}, ...]
    """
```

### Tool: `finish_exploration`

```python
def finish_exploration(understanding: str) -> None:
    """
    Signal that exploration is complete. Triggers outline generation.

    Args:
        understanding: Brief summary of what was learned
    """
```

## Phase 2: Outline Generation

After exploration, one LLM call generates the report structure.

```python
def generate_outline(prompt: str, exploration_summary: str, cached_files: list[str]) -> list[Section]:
    """
    Generate report outline based on exploration.

    Returns:
        List of sections, each with:
        - title: Section heading
        - focus: What this section should cover
        - relevant_files: Files likely relevant to this section
    """
```

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

```python
def generate_section(
    section: Section,
    prompt: str,
    store: Store,
    max_exploration_steps: int = 5
) -> str:
    """
    Generate one section of the report.

    The LLM can:
    - Use already-cached content
    - Do additional exploration via tools
    - Must cite everything with [path:line-line] format

    Returns:
        Markdown content for this section
    """
```

**Section generation is itself agentic:**
- LLM sees the section focus and relevant files
- Can call `read_file` to get more detail
- Can call `search_code` to find related code
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

```python
def assemble_report(sections: list[str], store: Store) -> tuple[str, list[str]]:
    """
    Combine sections and verify all citations.

    Returns:
        (final_report, invalid_citations)
    """
    report = "\n\n".join(sections)

    citations = extract_citations(report)
    invalid = []
    for cit in citations:
        if not citation_resolves(store, cit):
            invalid.append(cit)

    return report, invalid
```

If invalid citations exist, can either:
- Flag them in the output
- Re-generate affected sections with stricter instructions
- Accept best-effort output

## SQLite as Cache (Not Pre-computed Index)

Key difference from v1: SQLite stores **what was actually read**, not everything.

```sql
-- Files that have been read
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL,
    lang TEXT,
    content TEXT NOT NULL,  -- Full content for citation lookup
    read_at TEXT NOT NULL
);

-- Parsed chunks (for citation verification)
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id),
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    kind TEXT,  -- function, class, block
    text TEXT NOT NULL
);

-- Symbols (for get_symbols tool)
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id),
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL
);

-- FTS on cached content only
CREATE VIRTUAL TABLE chunks_fts USING fts5(text, content='chunks', content_rowid='id');
```

**The store grows as the LLM explores.** If the LLM only reads 10 files, only 10 files are indexed.

## Exploration Strategy

The LLM decides how to explore. Typical patterns:

**For "count Python files":**
```
1. list_files("*.py") → get count → done
```
1 tool call. No parsing needed.

**For "explain the authentication system":**
```
1. list_files("*") → see directory structure
2. list_files("*auth*") → find auth-related files
3. read_file("src/auth.py") → understand main auth
4. get_symbols("src/auth.py") → see functions
5. read_file("src/middleware.py") → see how it's used
6. finish_exploration("Auth uses JWT tokens, validated in middleware")
```
~6 tool calls. Only 2 files parsed.

**For comprehensive architecture doc:**
```
1. list_files("*") → directory structure
2. read_file("README.md") → project overview
3. list_files("src/**/*.py") → find all source
4. read_file("src/main.py") → entry point
5. get_symbols("src/main.py") → key functions
6. read_file("src/models.py") → data models
7. ... (more exploration based on what's found)
8. finish_exploration("...")
```
Maybe 15-20 tool calls for thorough exploration.

## LLM Call Budget

| Phase | Calls | Notes |
|-------|-------|-------|
| Exploration | O(files explored) | LLM-driven, typically 5-20 |
| Outline | 1 | Single structured output |
| Sections | O(sections) | One call per section, maybe more if section needs extra exploration |
| **Total** | ~15-30 | For a typical 5-10 section report |

Compare to v1: **1,100+ calls** for 100-file repo regardless of query.

## Citation Format

Same as before: `path:start_line-end_line`

But now citations are verified against the **cache of what was actually read**, not a pre-computed index of everything. If the LLM cites a file it didn't read, that's an invalid citation.

## Example Flow

**Prompt:** "Write documentation for the API endpoints in this Flask app"

**Phase 1 - Exploration:**
```
LLM: list_files("*.py")
Tool: ["app.py", "routes/users.py", "routes/orders.py", "models.py", "config.py"]

LLM: read_file("app.py")
Tool: [content of app.py - Flask app initialization]

LLM: list_files("routes/*.py")
Tool: ["routes/users.py", "routes/orders.py"]

LLM: read_file("routes/users.py")
Tool: [content - user CRUD endpoints]

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

## What's Different from tech-writer.py

| Aspect | tech-writer.py | v2 |
|--------|----------------|-----|
| Output length | Single LLM response | Arbitrary (section by section) |
| Exploration | Tool calls | Tool calls (same) |
| Storage | None (in memory) | SQLite cache |
| Citations | None | Required, verified |
| Structure | Flat | Outline → sections |

**v2 is tech-writer.py + sections + citations.**

## CLI

```bash
# Basic usage
python -m infinite_scalability --prompt prompt.md --repo /path/to/repo

# Remote repo
python -m infinite_scalability --prompt prompt.md --repo https://github.com/user/repo

# Control exploration depth
python -m infinite_scalability --prompt prompt.md --repo /path/to/repo --max-exploration 30

# Control output sections
python -m infinite_scalability --prompt prompt.md --repo /path/to/repo --max-sections 20
```

## Testing Strategy

1. **Unit tests:** Tool implementations, citation parsing, cache operations
2. **Integration tests:** End-to-end with mock LLM on small repos
3. **Exploration tests:** Verify LLM can find relevant files for known queries
4. **Citation tests:** Verify only readable content can be cited

## What's Removed (vs v1)

| Component | v1 | v2 | Reason |
|-----------|----|----|--------|
| Upfront ingest | Parse everything | Parse on read | Agentic exploration |
| Summarization | LLM per chunk | None | Never needed |
| DSPy | Cargo cult | Removed | Not useful |
| Embeddings | Fake (SHA256) | Removed | FTS sufficient |
| Per-claim grading | LLM per claim | None | Trust citations |

## Cost Comparison

| Scenario | v1 LLM Calls | v2 LLM Calls |
|----------|--------------|--------------|
| "Count Python files" | 1,100+ | 1-2 |
| "Explain auth system" | 1,100+ | ~10 |
| "Full architecture doc (10 sections)" | 1,100+ | ~25 |
| 1,000 file repo, simple query | 11,000+ | ~5 |

v2 cost scales with **query complexity**, not repo size.
