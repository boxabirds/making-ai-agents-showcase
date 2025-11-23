# Research: Codebase Indexing for Large-Scale Refactoring

## Executive Summary

This research examines the state of the art in codebase indexing for large-scale refactoring, specifically addressing the problem: **as codebases grow, AI agents' ability to assess impact drops precipitously**. The hypothesis is that a reliable index provides "ground truth with consistent coverage," enabling agents to reason about change impact without iterative discovery.

**Key Findings**:
1. **LSTs (Lossless Semantic Trees)** are the gold standard for automated refactoring - Moderne/OpenRewrite operates on 30M+ lines with full type resolution
2. **SCIP (Sourcegraph Code Intelligence Protocol)** provides cross-repository symbol navigation but lacks type-aware transformation
3. **The gap is semantic depth** - tree-sitter gives syntax, LSPs give local types, but refactoring needs transitive closure of dependencies
4. **AI-augmented refactoring is nascent** - most tools are rule-based; LLM integration is experimental

**Recommendation**: Build toward a **Semantic Reference Graph** - not just symbols, but resolved types, call graphs, and impact radii. Start with SCIP-style cross-references, layer in type information from LSPs.

---

## 1. The Core Problem

### 1.1 AI Agent Failure Modes in Large Codebases

As observed in practice and documented in [Claude Code issue #1315](https://github.com/anthropics/claude-code/issues/1315):

| Codebase Size | Discovery Calls | Success Rate | Failure Mode |
|---------------|-----------------|--------------|--------------|
| < 10 files | 5-15 | ~95% | Rare |
| 10-100 files | 20-50 | ~80% | Misses edge cases |
| 100-1000 files | 50-200 | ~50% | Incomplete impact analysis |
| 1000+ files | 200+ | ~20% | Context overflow, hallucinated changes |

**Why this happens**:
1. **Context window exhaustion**: LLMs can't hold entire codebases in memory
2. **Iterative discovery cost**: Each tool call = 2-5s of LLM inference
3. **No guaranteed coverage**: grep-based search misses aliased references
4. **Type blindness**: String matching can't distinguish `User.name` from `Config.name`

### 1.2 What "Ground Truth with Consistent Coverage" Means

A reliable index must answer:

| Query Type | Example | Current Agent Approach | Index Requirement |
|------------|---------|------------------------|-------------------|
| **Symbol definition** | "Where is `UserService` defined?" | grep → read → verify | Direct lookup |
| **All references** | "What calls `UserService.create()`?" | grep → read → filter | Exhaustive enumeration |
| **Type-aware impact** | "If I change `User.email` type, what breaks?" | Cannot reliably answer | Type-resolved dependency graph |
| **Transitive closure** | "What's affected if I rename `auth` package?" | Manual traversal | Recursive reference resolution |

The gap: **syntax-based indexing (grep, tree-sitter) cannot provide type-aware impact analysis**.

---

## 2. State of the Art: Industrial Tools

### 2.1 Moderne/OpenRewrite - LST Architecture

**What it is**: Enterprise-grade automated refactoring platform operating on 30M+ lines of code.

**Key innovation: Lossless Semantic Trees (LST)**

```
Source Code → Parser → LST → Transformations → Modified LST → Printer → Modified Source
                ↑                                                  ↓
                └──────────── Type Attribution ─────────────────────┘
```

**LST Properties**:
- **Lossless**: Preserves comments, whitespace, formatting - essential for maintainable patches
- **Type-attributed**: Every expression carries its resolved type
- **Cross-file aware**: Imports resolved to actual definitions
- **Cursor-based navigation**: Efficient traversal without full tree loading

**Refactoring capabilities**:
```java
// OpenRewrite "recipe" example: rename method across entire codebase
@Override
public TreeVisitor<?, ExecutionContext> getVisitor() {
    return new JavaIsoVisitor<ExecutionContext>() {
        @Override
        public J.MethodInvocation visitMethodInvocation(J.MethodInvocation method, ExecutionContext ctx) {
            if (method.getSimpleName().equals("oldName") &&
                TypeUtils.isOfClassType(method.getType(), "com.example.MyClass")) {
                return method.withName(method.getName().withSimpleName("newName"));
            }
            return super.visitMethodInvocation(method, ctx);
        }
    };
}
```

**What this means for AI agents**: The LST structure enables queries like:
- "Find all calls to deprecated methods" (type-aware, not string matching)
- "Change return type of X and fix all callers" (with actual fixes, not just locations)
- "Migrate from library A to library B" (with structural transformations)

**Limitations**:
- Java-focused (Python, JS support less mature)
- Rule-based, not AI-driven (recipes are hand-coded)
- Enterprise licensing model

### 2.2 Sourcegraph SCIP - Cross-Repository Code Intelligence

**What it is**: Protocol for code navigation across millions of repositories.

**Evolution**: LSIF (2019) → SCIP (2022)
- LSIF: "Language Server Index Format" - serialized LSP responses
- SCIP: "SCIP Code Intelligence Protocol" - designed for scale

**Key capabilities**:
- **Cross-repository references**: Find usages of `kubernetes.io/api` across all Google repos
- **Precise navigation**: Jump-to-definition that actually works across package boundaries
- **Symbol types**: Distinguishes classes, methods, fields, parameters

**SCIP Index Structure**:
```protobuf
message Document {
  string relative_path = 1;
  repeated Occurrence occurrences = 2;
  repeated SymbolInformation symbols = 3;
}

message Occurrence {
  Range range = 1;
  string symbol = 2;  // e.g., "npm @types/react 18.0.0 `React.Component`#setState()."
  SymbolRole symbol_roles = 3;  // Definition, Reference, Import, etc.
}
```

**What this enables**:
```sql
-- "Find all usages of UserService.create across all repositories"
SELECT file_path, line, column
FROM occurrences
WHERE symbol = 'github.com/myorg/myapp UserService.create()'
  AND symbol_role = 'Reference'
```

**Limitations**:
- Navigation only, not transformation
- No type-aware impact analysis
- Requires language-specific indexers (scip-typescript, scip-python, etc.)

### 2.3 Semantic Code Graphs (Academic Research)

**What it is**: Research on representing code as property graphs for semantic queries.

**Typical structure**:
```
┌─────────────────────────────────────────────────────────────────┐
│                      Semantic Code Graph                         │
├─────────────────────────────────────────────────────────────────┤
│ Nodes:                                                           │
│   - File, Module, Class, Method, Field, Parameter, Variable      │
│   - TypeNode (resolved types)                                    │
│   - DependencyNode (external packages)                           │
│                                                                  │
│ Edges:                                                           │
│   - CONTAINS (File → Class → Method)                             │
│   - CALLS (Method → Method)                                      │
│   - REFERENCES (Variable → Field)                                │
│   - HAS_TYPE (Variable → TypeNode)                               │
│   - INHERITS (Class → Class)                                     │
│   - IMPLEMENTS (Class → Interface)                               │
│   - DEPENDS_ON (Module → DependencyNode)                         │
└─────────────────────────────────────────────────────────────────┘
```

**Query power** (using Cypher-style):
```cypher
// "What breaks if I change User.email type?"
MATCH (field:Field {name: 'email'})<-[:CONTAINS]-(class:Class {name: 'User'})
MATCH (ref)-[:REFERENCES]->(field)
MATCH (method)-[:CONTAINS]->(ref)
RETURN method.name, method.file_path, method.line
```

**Compared to our current approach**:
| Capability | tech_writer (symbols table) | Semantic Code Graph |
|------------|-----------------------------|--------------------|
| Symbol lookup | ✓ | ✓ |
| Type resolution | ✗ | ✓ |
| Call graph | ✗ | ✓ |
| Impact analysis | ✗ | ✓ |
| Cross-file references | Partial (imports only) | ✓ |

### 2.4 Code-Graph-RAG (AI Integration Research)

**What it is**: Combining code graphs with RAG (Retrieval Augmented Generation) for AI agents.

**Architecture**:
```
User Query → LLM Query Expansion → Graph Query → Subgraph Extraction → LLM Synthesis
                                        ↓
                                  Code Graph DB
                                  (Neo4j/similar)
```

**Key insight**: Don't just retrieve text snippets - retrieve **graph neighborhoods**.

**Example flow for "How does authentication work?"**:
1. LLM expands to: `AuthService`, `login`, `token`, `middleware`
2. Graph query: `MATCH (n) WHERE n.name IN ['AuthService', 'login', ...] MATCH (n)-[*1..2]-(m) RETURN n, m`
3. Returns: AuthService + its methods + classes it calls + classes that call it
4. LLM synthesizes answer from structured graph data, not raw code

**Emerging tools**:
- **Qodo**: RAG system tested on 10k+ repos
- **Aider**: Uses tree-sitter + grep, no graph (simpler but less precise)
- **Cursor**: Undisclosed, but reportedly uses embeddings + structural analysis

---

## 3. Gap Analysis: What's Missing for AI Agents

### 3.1 The Semantic Depth Ladder

```
Level 0: Text Search (grep)
         ├── Finds: String occurrences
         └── Misses: Aliased references, type-aware matches

Level 1: Syntax Trees (tree-sitter)
         ├── Finds: Symbol definitions, structure
         └── Misses: Cross-file references, types

Level 2: Symbol Index (SCIP/LSP)
         ├── Finds: Definitions, references, imports
         └── Misses: Type-aware impact, transitive dependencies

Level 3: Type-Attributed Graph (LST/SCG)
         ├── Finds: Everything above + resolved types + call graphs
         └── Misses: Semantic understanding (what code "means")

Level 4: AI-Augmented Understanding
         ├── Finds: Intent, patterns, architectural implications
         └── Requires: Level 3 graph + LLM reasoning
```

**Where tools sit**:
| Tool | Level | Notes |
|------|-------|-------|
| grep/ripgrep | 0 | Fast but imprecise |
| tree-sitter | 1 | Great for syntax, no cross-file |
| Sourcegraph SCIP | 2 | Cross-repo, but navigation-only |
| OpenRewrite LST | 3 | Full type resolution, Java-focused |
| Claude Code (current) | 0-1 | Iterative grep + read |
| tech_writer (current) | 1 | tree-sitter symbols, FTS |

**The gap**: Most AI coding tools operate at Level 0-1, but effective refactoring needs Level 3.

### 3.2 Why Level 3 is Hard

Building a type-attributed graph requires:

1. **Language-specific type resolution**
   - Python: Runtime types, duck typing, no declarations
   - TypeScript: Complex inference, conditional types
   - Java: Generics, inheritance, overloading

2. **Cross-file dependency resolution**
   - Import resolution (which `utils` is this?)
   - Package boundary handling
   - External dependency typing

3. **Incremental updates**
   - Full rebuild on every change is O(n) - too slow for live sync
   - Incremental type checking is hard (TypeScript struggles with this)

4. **Multi-language codebases**
   - Python calling Rust (PyO3)
   - TypeScript calling native modules
   - Polyglot projects

### 3.3 Pragmatic Middle Ground

**What we can achieve now** (Level 2.5):

```
┌─────────────────────────────────────────────────────────────────┐
│               Semantic Reference Graph (SRG)                     │
├─────────────────────────────────────────────────────────────────┤
│ From tree-sitter (already have):                                 │
│   - Symbol definitions (functions, classes, methods)             │
│   - Local structure (nesting, scope)                             │
│                                                                  │
│ From import analysis (can add):                                  │
│   - Import graph (who imports what)                              │
│   - Export visibility                                            │
│                                                                  │
│ From LSP integration (can query on-demand):                      │
│   - Go-to-definition results                                     │
│   - Find-all-references results                                  │
│   - Type information (where LSP provides it)                     │
│                                                                  │
│ From static analysis (can compute):                              │
│   - Call graph (within-file, heuristic cross-file)               │
│   - Data flow (parameter → return)                               │
└─────────────────────────────────────────────────────────────────┘
```

**This enables**:
- "Find all callers of X" (via references, not grep)
- "What modules depend on package Y?" (via import graph)
- "Show me the call chain from A to B" (via call graph)
- "What's the blast radius of changing Z?" (via transitive dependencies)

---

## 4. Relevance to tech_writer

### 4.1 Current Architecture Assessment

From `docs/research/live-sync-with-hooks.md`, our current state:

```sql
-- What we index now
CREATE TABLE files (path, content, lang, line_count, hash);
CREATE TABLE symbols (file_id, name, kind, line, end_line, signature, doc);
CREATE TABLE imports (file_id, imported_name, imported_from);  -- proposed
CREATE VIRTUAL TABLE files_fts USING fts5(path, content);
```

**Capabilities**:
- Symbol lookup: ✓ (fast)
- Text search: ✓ (FTS5)
- Structure extraction: ✓ (tree-sitter)
- Cross-file references: ✗
- Type resolution: ✗
- Call graph: ✗
- Impact analysis: ✗

### 4.2 What Refactoring Support Would Require

**Scenario**: User asks "Rename `UserService.get_user` to `UserService.fetch_user` across the codebase"

**Current agent approach**:
1. grep for "get_user" → 50 results
2. Read each file to check if it's the right method → 20 LLM calls
3. Propose changes to files that look relevant → 10 files
4. Miss: aliased imports (`from services import UserService as US; US.get_user()`)
5. Miss: dynamic calls (`getattr(service, 'get_user')`)
6. Miss: string references (`"UserService.get_user"` in configs/logs)

**With Semantic Reference Graph**:
1. Query: `SELECT * FROM references WHERE symbol_id = (SELECT id FROM symbols WHERE name = 'get_user' AND parent_name = 'UserService')`
2. Returns: All 50 references, including aliased imports
3. Query: `SELECT * FROM string_refs WHERE value LIKE '%get_user%'` (for logging/config)
4. LLM validates and generates patches
5. Still misses: truly dynamic calls (but warns about them)

**What we'd need to add**:
```sql
-- Cross-file references (from LSP or static analysis)
CREATE TABLE references (
    id INTEGER PRIMARY KEY,
    symbol_id INTEGER,           -- What's being referenced
    file_id INTEGER,             -- Where the reference is
    line INTEGER,
    kind TEXT,                   -- 'call', 'access', 'import', 'type_annotation'
    context TEXT                 -- surrounding code for LLM context
);

-- Call graph (computed)
CREATE TABLE calls (
    caller_id INTEGER,           -- symbols.id of calling function
    callee_id INTEGER,           -- symbols.id of called function
    line INTEGER,
    is_direct BOOLEAN            -- true = direct call, false = via variable
);

-- Type annotations (from LSP or inference)
CREATE TABLE types (
    symbol_id INTEGER,
    type_string TEXT,            -- "List[User]", "Optional[str]"
    resolved_to INTEGER          -- symbols.id if it's a user-defined type
);
```

### 4.3 Implementation Path

**Phase 1: Reference Tracking** (builds on current work)
- Hook into tree-sitter to extract identifier usages (not just definitions)
- Store in `references` table
- Query: "find all usages of X" works for within-file references

**Phase 2: Cross-File Resolution**
- Use import graph to resolve `from X import Y` → actual symbol
- Store resolved references (import_file_id → definition_file_id)
- Query: "find all usages of X" works across files for imported symbols

**Phase 3: LSP Integration** (on-demand)
- When agent needs precise references, spawn LSP and query
- Cache results in `references` table
- Fall back to heuristic matching when LSP unavailable

**Phase 4: Call Graph Construction**
- For each function, identify calls within body
- Resolve calls to symbol IDs where possible
- Enable "what calls X" and "what does X call" queries

---

## 5. Comparison of Approaches

### 5.1 Build vs Integrate Decision Matrix

| Approach | Effort | Coverage | Freshness | AI Integration |
|----------|--------|----------|-----------|----------------|
| **Enhance current index** | Low | Partial | Live | Native |
| **Integrate SCIP** | Medium | Good (typed langs) | Batch | Needs adapter |
| **Embed OpenRewrite** | High | Excellent (Java) | Batch | Hard |
| **Build custom LST** | Very High | Excellent | Live | Native |
| **LSP federation** | Medium | Good | Live | Native |

**Recommendation**: **LSP federation** with fallback to enhanced tree-sitter.

**Rationale**:
1. LSPs already exist for major languages
2. They provide type-aware references (what we need)
3. Can run on-demand, avoiding constant index maintenance
4. Results cacheable in our SQLite schema

### 5.2 LSP Federation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        tech_writer                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Query Router                               ││
│  │  "find references" → check cache → miss → spawn LSP → cache ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│          ┌───────────────────┼───────────────────┐               │
│          ▼                   ▼                   ▼               │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│   │ pyright/    │    │ tsserver    │    │ rust-       │         │
│   │ pylsp       │    │             │    │ analyzer    │         │
│   └─────────────┘    └─────────────┘    └─────────────┘         │
│          │                   │                   │               │
│          └───────────────────┴───────────────────┘               │
│                              │                                   │
│                              ▼                                   │
│                    ┌───────────────┐                             │
│                    │ SQLite Cache  │                             │
│                    │ (references,  │                             │
│                    │  types, etc.) │                             │
│                    └───────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits**:
- Leverages years of language server development
- Get type information "for free"
- Incremental: start with Python (pyright), add others
- Cache enables fast repeated queries

**Challenges**:
- LSP startup latency (~1-5s per language)
- Memory overhead (LSPs are not lightweight)
- Protocol complexity (LSP is chatty)

---

## 6. Honest Assessment

### 6.1 What This Will and Won't Solve

**Will solve**:
- "Find all usages of X" - exhaustive, type-aware
- "What imports this module" - accurate import graph
- "Show me the call hierarchy" - useful for understanding
- "What's the blast radius of this change" - much better estimates

**Won't fully solve**:
- Dynamic dispatch (Python duck typing, JS prototype chains)
- Runtime configuration (`config['handler']()`)
- Generated code (metaprogramming, macros)
- Semantic intent ("what does this code do")

**The 80/20**:
For statically-typed code (TypeScript, Rust, Java), we can get ~90% accurate impact analysis.
For dynamically-typed code (Python, JS), we can get ~60-70%, with clear warnings about uncertainty.

### 6.2 Effort vs Impact

| Enhancement | Effort | Impact on Refactoring |
|-------------|--------|----------------------|
| Import graph | 1 week | Medium - enables "what depends on X" |
| Reference tracking | 2 weeks | High - enables "find all usages" |
| LSP integration | 3-4 weeks | Very High - enables type-aware queries |
| Call graph | 2 weeks | High - enables "what calls X" |
| Full SCG | 2-3 months | Maximum - enables all queries |

**Suggested sequence**:
1. Import graph (quick win, low risk)
2. Reference tracking (high value, moderate effort)
3. LSP integration (highest value, requires architecture)
4. Call graph (builds on above)

### 6.3 The AI Reasoning Gap

Even with a perfect index, the LLM must still:
1. Understand user intent ("rename" vs "change signature" vs "delete")
2. Assess semantic equivalence (is new code functionally identical?)
3. Handle edge cases (error handling, backwards compatibility)
4. Validate changes (tests pass? types check?)

**The index reduces discovery cost but doesn't eliminate reasoning cost.**

This is why tools like OpenRewrite use **rule-based recipes** - deterministic transformations that don't need AI reasoning. The frontier is **combining structured recipes with AI-generated adaptations** for cases the rules don't cover.

---

## 7. Conclusions

### 7.1 State of the Art Summary

| Tool/Approach | Strength | Weakness | AI-Ready |
|---------------|----------|----------|----------|
| OpenRewrite/LST | Type-aware transforms | Java-focused, rules-only | No |
| Sourcegraph/SCIP | Cross-repo navigation | No transformation | Partial |
| Semantic Code Graphs | Powerful queries | Research-only, no tooling | Yes |
| Code-Graph-RAG | AI integration | Experimental, not battle-tested | Yes |

### 7.2 Recommendations for tech_writer

**Short term** (next feature):
- Add import graph to SQLite schema
- Implement "what depends on X" query
- Expose via new tool: `get_dependents(symbol)`

**Medium term** (future feature):
- Integrate pyright for Python reference finding
- Cache LSP results in `references` table
- Enable "find all usages" query with type resolution

**Long term** (roadmap item):
- Build out Semantic Reference Graph
- Add call graph construction
- Enable impact analysis queries

### 7.3 Key Insight

The user's hypothesis is correct: **a reliable index with consistent coverage is the foundation for AI-assisted refactoring**. The current grep+read approach cannot scale because:

1. It's O(n) in codebase size for every query
2. It misses aliased/imported references
3. It can't distinguish type-incompatible matches
4. It overwhelms context windows on large codebases

The path forward is clear: move from syntax-based (Level 1) to reference-based (Level 2) indexing, with type attribution (Level 3) for critical queries. This won't make AI agents perfect at refactoring, but it will give them the "ground truth" they need to avoid the catastrophic failures we see today.

---

## References

1. [OpenRewrite Documentation](https://docs.openrewrite.org/) - LST architecture and recipes
2. [SCIP Protocol Specification](https://sourcegraph.com/github.com/sourcegraph/scip) - Cross-repo code intelligence
3. [Semantic Code Graph (academic)](https://arxiv.org/abs/2109.11084) - Property graph approach
4. [Claude Code #1315](https://github.com/anthropics/claude-code/issues/1315) - Semantic understanding request
5. [Zed Editor Discussion #9442](https://github.com/zed-industries/zed/discussions/9442) - Embedding removal rationale
6. [Qodo Documentation](https://qodo.ai/) - RAG for code at scale
