# Feature 4: Claude Code Prompt Enrichment

## Problem Statement

When users ask Claude Code questions about a codebase ("How does authentication work?", "Where is the database connection handled?"), the agent must iteratively discover relevant code through repeated tool calls:

1. grep for keywords → 50+ results
2. Read each promising file → 10-20 read calls
3. Analyze and filter → more greps and reads
4. Synthesize answer

This results in **30-50 LLM calls** for a single question, taking **60-250 seconds**.

The bottleneck is not tool execution (~10ms each) but **LLM inference** (2-5s per call). Each tool call requires a full LLM round-trip to decide the next action.

## User Pain Points

1. **Slow response times**: Simple questions take minutes instead of seconds
2. **Context window exhaustion**: Iterative discovery consumes tokens rapidly
3. **Inconsistent results**: Different runs may find different code paths
4. **Cost**: Each LLM call has API costs that compound quickly

## Proposed Solution

Enrich user prompts with pre-indexed code context **before** the LLM sees them. Using Claude Code's `UserPromptSubmit` hook, inject relevant symbols, file locations, and code snippets based on the user's query.

### How It Works

```
User types: "How does authentication work?"
                    │
                    ▼
         UserPromptSubmit Hook
                    │
                    ▼
        Semantic Query Expansion (fast LLM):
        - Input: natural language query
        - Output: {"symbols": ["auth", "login", "verify_token", "jwt"],
                   "file_patterns": ["*auth*", "*session*"],
                   "concepts": ["middleware", "oauth", "bearer"]}
                    │
                    ▼
        Query SQLite index with expanded terms:
        - Symbol search for each predicted name
        - File pattern matching
        - Import relationships
                    │
                    ▼
        Inject context into prompt:
        "## Relevant Code
         - class AuthMiddleware [src/auth/middleware.py:15]
         - function verify_token [src/auth/jwt.py:23]
         - function login_user [src/auth/views.py:12]"
                    │
                    ▼
        LLM sees enriched prompt, knows where to look
                    │
                    ▼
        3-5 targeted reads instead of 30-50 discovery calls
```

**Why semantic expansion?** Pattern-based keyword extraction ("authentication" → `["authentication"]`) cannot bridge semantic gaps. A cheap, fast LLM (~100ms, ~$0.00001/query) understands that "authentication" relates to `login`, `JWT`, `token`, `session`, etc.

### Expected Outcomes

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Tool calls per question | 30-50 | 3-5 | **90% reduction** |
| Response time | 60-250s | 10-25s | **5-10x faster** |
| Context usage | High (iterative) | Low (targeted) | Significant |

## User Stories

### US-1: Developer asking about codebase
**As a** developer using Claude Code
**I want** my questions about the codebase to be answered quickly
**So that** I can maintain flow while coding

**Acceptance Criteria**:
- Questions like "where is X defined?" return in <15 seconds
- Relevant file locations are included in the response
- No manual index building required (happens automatically)

### US-2: First-time codebase exploration
**As a** developer new to a codebase
**I want** Claude to have accurate knowledge of the code structure
**So that** I get reliable answers without the agent missing important files

**Acceptance Criteria**:
- Index is built on first session start
- All source files are included in the index
- Symbol definitions (functions, classes, methods) are extracted

### US-3: Ongoing development
**As a** developer actively modifying code
**I want** the index to stay current as I make changes
**So that** answers reflect the latest code state

**Acceptance Criteria**:
- Changes made through Claude (Write/Edit) update the index immediately
- External changes are detected and indexed (via file watcher)
- No manual refresh required

## Scope

### In Scope
- SQLite-based persistent index of symbols and content
- Tree-sitter parsing for symbol extraction
- Claude Code hook integration (SessionStart, PostToolUse, UserPromptSubmit)
- Import graph construction for cross-file awareness
- File watcher for external change detection
- Support for: Python, JavaScript, TypeScript, Go, Rust, Ruby, Java, PHP, C++

### Out of Scope
- Full type resolution (LSP-level accuracy)
- Semantic embeddings / vector search
- Call graph construction (future enhancement)
- Multi-repository support

## Success Metrics

1. **Tool call reduction**: 80%+ reduction in LLM calls for "find X" queries
2. **Response time**: <15s for symbol lookup questions
3. **Index freshness**: <1s delay between file change and index update
4. **Coverage**: >95% of definitions captured for supported languages

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hook timeout (60s limit) | Index build may fail | Incremental indexing, background processing |
| Large codebases overwhelm context | Injected context too big | Relevance scoring, top-K filtering |
| Tree-sitter grammar gaps | Missing symbols | Fallback to regex patterns |
| File watcher overhead | Performance impact | Debouncing, selective watching |

## Dependencies

- Claude Code CLI with hook support
- Tree-sitter grammars for target languages
- SQLite (already used in tech_writer)
- watchdog library for file system events
