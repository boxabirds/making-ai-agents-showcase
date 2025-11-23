# Tech Design: Codebase Complexity Analyzer

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Entry Point                              │
│  (CLI: repo path/URL → JSON complexity report)                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      File Discovery                              │
│  - Walk directory with .gitignore support                        │
│  - Filter by extension → language mapping                        │
│  - Skip binary files                                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Tree-sitter Parsing                         │
│  - Parse each file with appropriate language grammar             │
│  - Handle parse failures gracefully                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Normalized AST Mapping                        │
│  - Map language-specific nodes to universal concepts             │
│  - UN_Function, UN_If, UN_Loop, UN_Switch, UN_BooleanOp          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Metric Calculation                            │
│  - Cyclomatic complexity per function                            │
│  - Cognitive complexity with nesting penalty                     │
│  - Max nesting depth                                             │
│  - Aggregation to file and repo level                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       JSON Output                                │
│  - Summary metrics                                               │
│  - Distribution histogram                                        │
│  - Top complex functions                                         │
└─────────────────────────────────────────────────────────────────┘
```

## Normalized AST Mapping

The key insight is that different languages use different node names for the same constructs. We define a normalization layer:

```toml
# normalized_nodes.toml

[UN_Function]
python = ["function_definition"]
javascript = ["function_declaration", "method_definition", "arrow_function"]
typescript = ["function_declaration", "method_definition", "arrow_function"]
go = ["function_declaration", "method_declaration"]
rust = ["function_item"]
java = ["method_declaration"]

[UN_If]
python = ["if_statement"]
javascript = ["if_statement"]
typescript = ["if_statement"]
go = ["if_statement"]
rust = ["if_expression", "if_let_expression"]
java = ["if_statement"]

[UN_Loop]
python = ["for_statement", "while_statement"]
javascript = ["for_statement", "for_in_statement", "for_of_statement", "while_statement", "do_statement"]
typescript = ["for_statement", "for_in_statement", "for_of_statement", "while_statement", "do_statement"]
go = ["for_statement"]
rust = ["for_expression", "while_expression", "loop_expression"]
java = ["for_statement", "while_statement", "do_statement", "enhanced_for_statement"]

[UN_Switch]
python = ["match_statement"]  # Python 3.10+
javascript = ["switch_statement"]
typescript = ["switch_statement"]
go = ["expression_switch_statement", "type_switch_statement"]
rust = ["match_expression"]
java = ["switch_expression", "switch_statement"]

[UN_Try]
python = ["try_statement"]
javascript = ["try_statement"]
typescript = ["try_statement"]
go = []  # Go uses explicit error returns
rust = []  # Rust uses Result/Option
java = ["try_statement"]

[UN_BooleanOp]
# Binary expressions with && || and or
python = ["boolean_operator"]  # Check operator: and, or
javascript = ["binary_expression"]  # Check operator: &&, ||
typescript = ["binary_expression"]
go = ["binary_expression"]
rust = ["binary_expression"]
java = ["binary_expression"]
```

## Complexity Calculation Algorithm

```python
def calculate_cyclomatic_complexity(function_node, language):
    """
    Cyclomatic complexity = 1 + number of decision points

    Decision points:
    - if/elif/else if
    - for/while/do-while loops
    - switch/match cases
    - catch/except handlers
    - && and || operators (each adds 1)
    - ternary expressions
    """
    complexity = 1

    for node in walk_descendants(function_node):
        node_type = node.type

        if is_decision_point(node_type, language):
            complexity += 1

        if is_boolean_operator(node, language):
            complexity += 1

    return complexity


def calculate_cognitive_complexity(function_node, language):
    """
    Cognitive complexity = cyclomatic + nesting penalty

    When a decision point is nested inside another:
    - Add (1 + nesting_level) instead of just 1

    This penalizes deeply nested code more heavily.
    """
    complexity = 0

    def visit(node, nesting_level):
        nonlocal complexity
        node_type = node.type

        if is_decision_point(node_type, language):
            # Add base + nesting penalty
            complexity += 1 + nesting_level

            # Recurse into children with increased nesting
            for child in node.children:
                visit(child, nesting_level + 1)
        else:
            # Continue without increasing nesting
            for child in node.children:
                visit(child, nesting_level)

    visit(function_node, 0)
    return complexity
```

## File Structure

### Python Implementation

```
pocs/code-base-complexity/
├── PRD.md
├── TECH_DESIGN.md
├── tasks.md
├── complexity_analyzer.py      # Main Python implementation
├── normalized_nodes.py         # Node mapping definitions
├── rust/                       # Rust implementation
│   ├── Cargo.toml
│   └── src/
│       └── main.rs
├── run_comparison.sh           # Compare Python vs Rust
└── test_repos.sh               # Test against axios and fastapi
```

### Python: `complexity_analyzer.py`

Key components:
- `FileDiscovery` - Uses pathspec for .gitignore support
- `LanguageDetector` - Extension → language mapping
- `ComplexityCalculator` - Tree-sitter parsing + metrics
- `ReportGenerator` - JSON output

### Rust: `rust/src/main.rs`

Key components:
- Uses `ignore` crate for .gitignore-aware walking (same as ../rust/)
- Uses `tree-sitter` crate + language grammars
- Reuses `clone_or_update_repo` pattern from ../rust/main.rs
- Parallel processing with `rayon`

## Comparison Strategy

Both implementations should produce identical JSON output structure. The comparison script:

1. Runs Python analyzer on repo → `output_py.json`
2. Runs Rust analyzer on same repo → `output_rs.json`
3. Compares:
   - Total counts match
   - Top 10 complex functions match
   - Complexity scores within 0.1% tolerance (floating point)
4. Reports timing difference

## Complexity Score Buckets

For integration with tech_writer:

```python
def get_complexity_bucket(score: float) -> tuple[str, dict]:
    """Map complexity score to documentation budget."""
    if score < 20:
        return "simple", {
            "max_sections": 5,
            "max_exploration": 50,
            "description": "Small, focused codebase"
        }
    elif score < 50:
        return "medium", {
            "max_sections": 15,
            "max_exploration": 200,
            "description": "Moderate complexity codebase"
        }
    else:
        return "complex", {
            "max_sections": 50,
            "max_exploration": 500,
            "description": "Large, complex codebase"
        }
```

## .gitignore Support

### Python
Using `pathspec` library (already a dependency):
```python
import pathspec

def load_gitignore(repo_root: Path) -> pathspec.PathSpec:
    gitignore_path = repo_root / ".gitignore"
    patterns = []
    if gitignore_path.exists():
        patterns = gitignore_path.read_text().splitlines()
    # Add standard ignores
    patterns.extend([".git", "__pycache__", "node_modules", "*.pyc"])
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
```

### Rust
Using `ignore` crate (already used in ../rust/):
```rust
use ignore::WalkBuilder;

let walker = WalkBuilder::new(repo_root)
    .hidden(false)
    .git_ignore(true)
    .git_global(false)
    .git_exclude(false)
    .filter_entry(|e| e.file_name() != ".git")
    .build();
```

## Performance Considerations

1. **Parallel parsing** - Files can be parsed independently
   - Python: `concurrent.futures.ProcessPoolExecutor`
   - Rust: `rayon::par_iter()`

2. **Lazy language loading** - Only load tree-sitter grammars for detected languages

3. **Early termination** - Skip files that fail to parse without blocking others

4. **Memory efficiency** - Process files in streaming fashion, don't hold all ASTs in memory
