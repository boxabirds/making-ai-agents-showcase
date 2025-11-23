# What's the best way to assess code base complexity? 

Short version: **Tree-sitter + a thin normalization layer is pretty much the sweet spot** for “any language” complexity, and it works well in both Python and Rust. The trick is to (1) define *language-agnostic* metrics over a *normalized AST*, and (2) design the scanner so you can empirically see whether IO or CPU is the bottleneck.

---

## 1. What are you actually measuring?

For a GitHub repo across arbitrary languages, you want:

### File-level metrics

* **Physical size**

  * Lines of code (LOC)
  * Logical LOC (non-blank, non-comment)
  * Token count
* **Parse-ability**

  * “Parsed OK” vs “parse failed” (good for filtering generated / broken stuff)

These are cheap and already tell you a lot (e.g. ratio of generated to hand-written code, large blobs, etc).

### Function / method-level metrics

The “classic” set that maps cleanly to tree-sitter:

* **Cyclomatic complexity** per function:
  `M = 1 + # of decision points`
  Count nodes like: `if`, `else if`, `for`, `while`, `case`, `catch`, ternaries, logical `&&`/`||`, etc.
* **Max nesting depth** (block nesting, conditionals, loops)
* **Parameters**

  * Parameter count
  * Optional vs required (if your node type exposes this)
* **Function size**

  * LOC / tokens in function body
  * Number of statements
* **Cognitive-ish complexity** (Sonar-style)

  * Cyclomatic + extra penalty on nested control flow
  * Penalty for multiple boolean operators in a single condition

### Aggregate repo-level metrics

Then you aggregate up:

* Distributions:

  * Complexity histogram of functions
  * 95th percentile complexity / nesting depth
  * Outliers: “top N most complex functions”
* Per-module / per-directory stats
* “Smell” flags:

  * Functions with complexity > threshold
  * Files with crazy function counts or giant functions

That’s enough to generate quite meaningful “complexity maps” across languages without tying yourself to language-specific semantics.

---

## 2. Why tree-sitter is a good core

Tree-sitter gives you:

* **Multi-language** with consistent API and grammars for most things you care about (C-family, JS/TS, Python, Rust, Go, Java, etc).
* **Concrete-ish AST** vs regex/line-based heuristics → much more robust.
* **Fast incremental parsing** if you ever want to do “watch repo” mode later.

The missing piece is that **each language uses different node names** for the same constructs. You solve that with a tiny “normalization layer”.

### Normalized AST / “uAST-lite” concept

You don’t need a full-blown universal AST – just a small mapping like:

```text
UN_Function:
  - tree_sitter_languages: 
      - javascript: function_declaration, method_definition, arrow_function
      - typescript: function_declaration, method_signature, ...
      - python: function_definition
      - rust: function_item, impl_item (method)
      - go: function_declaration, method_declaration
      ...
UN_If:
  - javascript: if_statement
  - python: if_statement
  - rust: if_expression, if_let_expression
UN_ForLoop:
  - javascript: for_statement, for_in_statement, for_of_statement
  - python: for_statement
  - rust: for_expression, for_in_expression
UN_WhileLoop:
  - javascript: while_statement, do_statement
  - python: while_statement
  - rust: while_expression, loop_expression (only if used as loop)
UN_SwitchLike:
  - javascript: switch_statement
  - rust: match_expression
  - etc.
UN_BooleanOp:
  - binary_expression with operator in {&&, ||, and, or}
```

You can encode those as **tree-sitter queries** (`.scm` files) or as simple maps in code. Then your metric code operates purely on `UN_*` categories and doesn’t care what the underlying language is.

### Complexity formula with tree-sitter

Per function (normalized):

* Start with `complexity = 1`
* For every child node of types:

  * `UN_If`, `UN_ForLoop`, `UN_WhileLoop`, `UN_SwitchLike`, `UN_Catch`, `UN_Ternary` → `complexity += 1`
  * For each `UN_BooleanOp` beyond the first in a single condition → `complexity += 1`
* For cognitive-style complexity:

  * Maintain a `nesting_level` as you descend into `UN_If` / loops / `UN_SwitchLike`
  * When you hit a decision at `nesting_level > 0`, add `1 + nesting_level` instead of 1
* Track max depth as you recurse.

This is deterministic, easy to test, and extensible per language.

---

## 3. Architecture so you can test IO vs CPU (Python & Rust)

You want the same **pipeline design** in both languages:

### Pipeline

1. **File discovery**

   * Walk the repo with:

     * Python: `os.walk()` or `pathlib.Path.rglob('*')`
     * Rust: `ignore` crate (`WalkBuilder`) which respects `.gitignore` and is very fast.
   * Filter out:

     * Binary files
     * Huge files (e.g. > 2–5 MB)
     * Non-source (by extension or via a language map similar to GitHub Linguist)

2. **Language detection**

   * Simplest: map from file extension to Tree-sitter language.
   * Optional: integrate GitHub Linguist or a smaller rule-based classifier if you need weird extensions.

3. **Parsing**

   * For each file, read the whole text into memory.
   * Run tree-sitter parse for that language.
   * If parsing fails → mark, skip metrics, maybe still record LOC.

4. **Metric calculation**

   * Walk the AST to:

     * Find function-like nodes (per language map)
     * For each function node, recursively traverse children to compute:

       * Cyclomatic / cognitive complexity
       * Nesting depth
       * LOC within function (you can use `node.start_byte`, `end_byte` and count newlines)
       * Parameter count
   * Store results in a per-function record like:

     ```json
     {
       "file": "src/foo/bar.rs",
       "function_name": "do_something",
       "start_line": 120,
       "end_line": 180,
       "complexity": 14,
       "cognitive_complexity": 21,
       "max_nesting": 4,
       "parameters": 3
     }
     ```

5. **Aggregation**

   * Aggregate in-memory or stream to a SQLite DB / parquet / JSONL, then run analysis.

### Measuring IO vs CPU

Because you’re interested in bottlenecks, you can design **three passes**:

1. **IO-only baseline**

   * Walk files, read them into memory, count bytes / LOC, but do no parsing.
   * Measure:

     * total time
     * bytes read
     * number of files
   * This gives you the bare IO cost.

2. **Parse-only**

   * Same as above but run tree-sitter parse and *do not* compute metrics—just discard the AST.
   * This isolates parsing cost on top of IO.

3. **Parse + metrics**

   * Full pipeline.
   * Now you can see how much extra time the complexity computation adds.

For each, measure in both Python and Rust with (roughly) the same parallelism:

* Python:

  * `concurrent.futures.ProcessPoolExecutor` (multiprocessing to avoid GIL), chunk by files.
* Rust:

  * `rayon` to parallelize over the file list.

Then compare:

* Throughput: files/sec, LOC/sec
* CPU utilization vs disk usage (if you want to go deeper, sample with `perf`/`py-spy` vs `cargo flamegraph`)

My prediction:

* Rust version: CPU-bound on parsing + metrics for large repos, IO-bound on small ones.
* Python version: likely CPU-bound earlier because of interpreter overhead, but IO can still dominate on spinning disks or network FS.

---

## 4. Implementation notes: Python

Core pieces:

* **Tree-sitter bindings**:

  * `tree_sitter` + language bundles (`tree_sitter_languages` or custom).
* **Structure**:

  * `repo_scanner.py` – produce file list & language mapping
  * `parser.py` – file → AST
  * `metrics.py` – AST → complexity metrics
  * `runner.py` – orchestrate passes, parallelism, timing

Pseudo-structure:

```python
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from tree_sitter import Language, Parser

LANG = Language("build/my-languages.so", "python")
parser = Parser()
parser.set_language(LANG)

def analyze_file(path: Path):
    src = path.read_bytes()
    tree = parser.parse(src)
    # walk AST to find functions and compute metrics...
    return metrics_for_file

def main(root: Path):
    files = discover_source_files(root)  # extension filter, etc.
    with ProcessPoolExecutor() as ex:
        results = list(ex.map(analyze_file, files))
    # aggregate and print/save
```

**Normalization**: for each language, define:

```python
LANGUAGE_NODE_MAP = {
    "python": {
        "function_nodes": ["function_definition"],
        "if_nodes": ["if_statement"],
        "loop_nodes": ["for_statement", "while_statement"],
        "switch_nodes": [],
        "boolean_binary_nodes": [("boolean_operator", "and"), ("boolean_operator", "or")],
    },
    ...
}
```

Or encode as tree-sitter queries (`.scm`) and use `Query` objects to match.

---

## 5. Implementation notes: Rust

Core crates:

* `tree-sitter` + language-specific crates (`tree-sitter-python`, `tree-sitter-javascript`, etc.)
* `ignore` for walking repos with `.gitignore` awareness
* `rayon` for parallelism

Very similar structure:

```rust
use ignore::WalkBuilder;
use rayon::prelude::*;
use tree_sitter::{Language, Parser};

extern "C" { fn tree_sitter_python() -> Language; }

fn analyze_file(path: &Path) -> FileMetrics {
    let src = std::fs::read(path).unwrap();
    let mut parser = Parser::new();
    parser.set_language(unsafe { tree_sitter_python() }).unwrap();
    let tree = parser.parse(&src, None).unwrap();
    // walk AST, compute metrics...
}

fn main() {
    let files: Vec<_> = WalkBuilder::new(".")
        .types(...) // restrict to known languages
        .build()
        .filter_map(|e| e.ok())
        .map(|e| e.into_path())
        .collect();

    let metrics: Vec<_> = files.par_iter()
        .map(|path| analyze_file(path))
        .collect();

    // aggregate & output
}
```

Again, you share the **normalization spec** between Python and Rust (e.g., a JSON/ TOML file listing which node types correspond to which `UN_*` concept) so both implementations compute *exactly the same* metrics.

---

## 6. Alternatives / complements

For completeness:

* **Text-based tools**:

  * e.g. `lizard`, `scc`, `tokei` – very fast, but either language-limited or line/token heuristics. Good baseline for performance sanity checks; less fine-grained than a tree-sitter AST approach.
* **CFG-based complexity** (true McCabe via control-flow graph):

  * More precise but a lot more work and highly language-specific. For “any language” it’s usually overkill.
* **Semantic complexity** (e.g. via CodeQL / static analyzers):

  * Great, but heavy, very language-specific, and not trivial to embed in your own Rust + Python implementations.

Given your goals (multi-language, own implementation, IO vs CPU comparison), **tree-sitter + a thin cross-language normalization + AST-based cyclomatic/cognitive metrics** is a very solid, scalable approach.

---

If you like, next step I can do is sketch a concrete **normalization spec (e.g. TOML)** plus a **sample Python AST walker** that uses it to compute cyclomatic & cognitive complexity for, say, JS, Python, and Rust with identical logic.
