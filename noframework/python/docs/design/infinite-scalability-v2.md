# Infinite-Scalability Tech Writer Agent v2

## Goals
- Handle arbitrary-size codebases without context overruns.
- Produce citation-backed reports with verifiable references.
- Minimize LLM calls: O(1) for simple queries, O(iterations) for complex ones.
- Primary output is a single Markdown file; SQLite is per-run working state only.

## Design Principles

1. **No eager processing.** Don't summarize, embed, or transform anything until the query demands it.
2. **Retrieval-first.** Parse and index for search; let the query drive what gets sent to the LLM.
3. **Batch LLM calls.** One call to draft, one call to verify. Not one call per chunk/claim.
4. **Simple orchestration.** No framework abstractions that don't add value.

## Architecture Overview

```
User Prompt
    │
    ▼
┌─────────────────┐
│  Ingest & Index │  ← Tree-sitter parse, FTS index, symbol graph
│  (no LLM calls) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Retrieve     │  ← FTS + symbol lookup + graph expansion
│  (no LLM calls) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Draft Report   │  ← 1 LLM call: prompt + retrieved chunks → report with citations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Verify Citations│  ← Deterministic: check citations resolve to stored chunks
│  (no LLM calls) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Quality Gate   │  ← If citations invalid or coverage low, iterate (bounded)
└────────┬────────┘
         │
         ▼
    Final Report
```

**Total LLM calls:** 1 per iteration. Max iterations bounded (default: 3).

## Pipeline Stages

### 1. Ingest (deterministic, no LLM)

Walk the repo, parse with tree-sitter, store:
- `files`: path, hash, lang, size, mtime
- `chunks`: file_id, start_line, end_line, kind, text, hash
- `symbols`: file_id, name, kind, signature, line range
- `edges`: symbol relationships (imports, calls, inheritance)

**FTS index:** `chunks_fts` on chunk text for lexical search.

No summarization. No embeddings. Just structured storage for retrieval.

### 2. Retrieve (deterministic, no LLM)

Given user prompt, gather relevant chunks:

1. **Lexical search:** FTS on chunks matching prompt keywords.
2. **Symbol lookup:** Find symbols matching prompt terms (exact/regex/fuzzy).
3. **Graph expansion:** Follow edges from matched symbols (imports, callers, etc.).
4. **File path matching:** Include chunks from files whose paths match prompt terms.
5. **Dedupe and rank:** Score by relevance (FTS rank + symbol match + graph proximity).
6. **Budget:** Return top-K chunks that fit within context budget.

**Output:** `RetrievedContext(chunks, symbols, edges)` with citation-ready references.

### 3. Draft Report (1 LLM call)

Single LLM call with:
- User prompt
- Retrieved chunks as evidence (each with `path:start-end` citation)
- Instructions to cite evidence and not invent content

**Prompt structure:**
```
System: You are a technical writer. Use only the provided evidence.
        Every statement must cite evidence using [path:start-end] format.

User: {user_prompt}

Evidence:
[src/foo.py:10-25] def calculate_total(...): ...
[src/bar.py:5-15] class OrderManager: ...
...

Write a report addressing the prompt. Cite every claim.
```

**Output:** Markdown report with inline citations.

### 4. Verify Citations (deterministic, no LLM)

For each citation in the report:
1. Parse `path:start-end` format.
2. Look up file by path in store.
3. Find chunk covering the line range.
4. If not found → invalid citation.

**Output:** List of valid/invalid citations.

### 5. Quality Gate (deterministic)

Check:
- All citations valid (resolve to stored chunks)
- Coverage threshold met (enough of the prompt addressed)
- No hallucinated file paths

If failed and iterations < max:
- Re-draft with feedback about invalid citations
- Include only valid evidence

If failed at max iterations:
- Emit partial report with warnings

## Data Model

```python
@dataclass
class FileRecord:
    id: int | None
    path: str
    hash: str
    lang: str
    size: int
    mtime: datetime
    parsed: bool

@dataclass
class ChunkRecord:
    id: int | None
    file_id: int
    start_line: int
    end_line: int
    kind: str  # function, class, method, block
    text: str
    hash: str

@dataclass
class SymbolRecord:
    id: int | None
    file_id: int
    name: str
    kind: str  # function, class, import, variable
    signature: str | None
    start_line: int
    end_line: int
    doc: str | None
    parent_symbol_id: int | None

@dataclass
class EdgeRecord:
    src_symbol_id: int
    dst_symbol_id: int
    edge_type: str  # imports, calls, inherits, uses

@dataclass
class RetrievedContext:
    chunks: list[ChunkRecord]
    symbols: list[SymbolRecord]
    edges: list[EdgeRecord]

@dataclass
class ReportVersion:
    id: int | None
    content: str
    created_at: datetime
    valid_citations: int
    invalid_citations: int
    iteration: int
```

## DB Schema

```sql
-- Core tables
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL,
    lang TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime TEXT NOT NULL,
    parsed INTEGER DEFAULT 1
);

CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    hash TEXT NOT NULL
);

CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    signature TEXT,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    doc TEXT,
    parent_symbol_id INTEGER REFERENCES symbols(id)
);

CREATE TABLE edges (
    src_symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    dst_symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    edge_type TEXT NOT NULL,
    PRIMARY KEY (src_symbol_id, dst_symbol_id, edge_type)
);

CREATE TABLE report_versions (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    valid_citations INTEGER DEFAULT 0,
    invalid_citations INTEGER DEFAULT 0,
    iteration INTEGER DEFAULT 0
);

-- FTS for chunk search
CREATE VIRTUAL TABLE chunks_fts USING fts5(text, content='chunks', content_rowid='id');

-- Indexes
CREATE INDEX idx_chunks_file ON chunks(file_id);
CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_symbols_file ON symbols(file_id);
CREATE INDEX idx_edges_src ON edges(src_symbol_id);
CREATE INDEX idx_edges_dst ON edges(dst_symbol_id);
```

## Retrieval Strategy

### Context Budget

Modern LLMs have large context windows (128K+ tokens). Use them.

```python
MAX_CONTEXT_TOKENS = 100_000  # Leave room for prompt and response
TOKENS_PER_CHAR = 0.25  # Rough estimate

def fits_budget(chunks: list[ChunkRecord], budget: int = MAX_CONTEXT_TOKENS) -> bool:
    total_chars = sum(len(c.text) for c in chunks)
    return total_chars * TOKENS_PER_CHAR < budget
```

### Retrieval Algorithm

```python
def retrieve(store: Store, prompt: str, budget: int = MAX_CONTEXT_TOKENS) -> RetrievedContext:
    scored: dict[int, float] = {}

    # 1. FTS search
    for chunk in store.search_fts(prompt, limit=50):
        scored[chunk.id] = scored.get(chunk.id, 0) + 1.0

    # 2. Symbol lookup
    symbols = store.search_symbols(prompt, limit=20)
    for sym in symbols:
        for chunk in store.get_chunks_for_file(sym.file_id):
            if chunk.start_line <= sym.end_line and chunk.end_line >= sym.start_line:
                scored[chunk.id] = scored.get(chunk.id, 0) + 0.5

    # 3. Graph expansion
    edges = store.get_edges_for_symbols([s.id for s in symbols])
    neighbor_ids = {e.dst_symbol_id for e in edges} | {e.src_symbol_id for e in edges}
    for sym_id in neighbor_ids:
        sym = store.get_symbol(sym_id)
        if sym:
            for chunk in store.get_chunks_for_file(sym.file_id):
                scored[chunk.id] = scored.get(chunk.id, 0) + 0.25

    # 4. Rank and budget
    ranked = sorted(scored.items(), key=lambda x: -x[1])
    selected = []
    for chunk_id, score in ranked:
        chunk = store.get_chunk(chunk_id)
        if fits_budget(selected + [chunk], budget):
            selected.append(chunk)
        else:
            break

    return RetrievedContext(chunks=selected, symbols=symbols, edges=edges)
```

## LLM Interface

Single function, single responsibility:

```python
def draft_report(prompt: str, evidence: list[tuple[str, str]]) -> str:
    """
    Draft a report with citations.

    Args:
        prompt: User's request
        evidence: List of (citation, text) tuples

    Returns:
        Markdown report with inline citations
    """
    evidence_block = "\n\n".join(f"[{cit}]\n{text}" for cit, text in evidence)

    response = llm_call(
        system=SYSTEM_PROMPT,
        user=f"Prompt: {prompt}\n\nEvidence:\n{evidence_block}\n\nWrite the report.",
    )
    return response

SYSTEM_PROMPT = """You are a technical writer producing documentation from source code.

Rules:
1. Use ONLY the provided evidence. Do not invent facts.
2. Every statement must cite evidence using [path:start-end] format.
3. If evidence is insufficient, say so explicitly rather than guessing.
4. Match the style and scope requested in the prompt.
"""
```

## Citation Format

Standard format: `path:start_line-end_line`

Examples:
- `src/auth.py:10-25`
- `lib/utils/helpers.ts:100-150`

Validation:
```python
def validate_citation(citation: str) -> tuple[str, int, int]:
    """Parse and validate citation format. Raises ValueError if invalid."""
    match = re.match(r'^(.+):(\d+)-(\d+)$', citation)
    if not match:
        raise ValueError(f"Invalid citation format: {citation}")
    path, start, end = match.groups()
    return path, int(start), int(end)

def citation_resolves(store: Store, citation: str) -> bool:
    """Check if citation points to a real chunk in the store."""
    try:
        path, start, end = validate_citation(citation)
    except ValueError:
        return False
    file_rec = store.get_file_by_path(path)
    if not file_rec:
        return False
    chunk = store.find_chunk_covering(file_rec.id, start, end)
    return chunk is not None
```

## Iteration Loop

```python
MAX_ITERATIONS = 3

def generate_report(store: Store, prompt: str) -> str:
    context = retrieve(store, prompt)
    evidence = [(make_citation(c, store), c.text) for c in context.chunks]

    for iteration in range(MAX_ITERATIONS):
        report = draft_report(prompt, evidence)

        # Verify citations
        citations = extract_citations(report)
        valid = [c for c in citations if citation_resolves(store, c)]
        invalid = [c for c in citations if not citation_resolves(store, c)]

        store.save_report_version(report, len(valid), len(invalid), iteration)

        if not invalid:
            return report  # Success

        # Retry with feedback
        evidence = [(c, get_chunk_text(store, c)) for c in valid]
        prompt = f"{prompt}\n\nPrevious attempt had invalid citations: {invalid}. Use only provided evidence."

    return report  # Best effort after max iterations
```

## CLI

```bash
# Basic usage
python -m infinite_scalability --prompt prompt.md --repo /path/to/repo

# Remote repo
python -m infinite_scalability --prompt prompt.md --repo https://github.com/user/repo

# Persist working store for debugging
python -m infinite_scalability --prompt prompt.md --repo /path/to/repo --persist-store

# Output to specific file
python -m infinite_scalability --prompt prompt.md --repo /path/to/repo --output report.md
```

## What's Removed (vs v1)

| Component | v1 | v2 | Reason |
|-----------|----|----|--------|
| Chunk summarization | LLM per chunk | None | Unused, expensive |
| File summarization | LLM per file | None | Unused, expensive |
| Module/package summaries | String concat | None | Pretending to be useful |
| DSPy | Imported, unused | Removed | Cargo cult |
| Embeddings | SHA256 hashes | Removed | Not actually embeddings |
| Per-claim grading | LLM per claim | Batch or none | O(claims) → O(1) |
| Per-line enforcement | Retrieval per line | Single pass | O(lines) → O(1) |

## Cost Comparison

| Scenario | v1 LLM Calls | v2 LLM Calls |
|----------|--------------|--------------|
| 100 files, 10 chunks each | 1,100+ | 1-3 |
| 1,000 files, 10 chunks each | 11,000+ | 1-3 |
| Simple query | 1,100+ | 1 |
| Complex query needing revision | 1,463+ | 3 |

## Future Extensions (not in v2 scope)

These are explicitly **not implemented** in v2, but could be added if needed:

1. **Real embeddings:** If FTS recall is insufficient, add sentence-transformer embeddings. But prove it's needed first.

2. **Streaming:** For very large reports, stream generation. But most reports fit in a single response.

3. **Caching:** Cache ingest results across runs for unchanged files. But per-run stores are simpler to reason about.

4. **Parallel ingest:** Tree-sitter parsing is fast; parallelization is premature optimization.

## Testing Strategy

1. **Unit tests:** Citation parsing, retrieval ranking, FTS queries
2. **Integration tests:** End-to-end on small fixture repos
3. **Golden tests:** Known repo + prompt → expected report structure

No need for mock LLM tests for summarization because there is no summarization.
