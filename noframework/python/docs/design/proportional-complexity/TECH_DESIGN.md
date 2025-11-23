# Tech Design: Proportional Complexity

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           tech_writer CLI                                │
│  python -m tech_writer --repo https://github.com/owner/repo             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      1. Repository Resolution                            │
│  - Clone/update repo to ~/.cache/github/owner/repo                      │
│  - Return local path                                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      2. Complexity Analysis (NEW)                        │
│  - Run: complexity-analyzer --path /local/repo --output json            │
│  - Parse JSON: extract total_cyclomatic_complexity                      │
│  - Map to budget: simple/medium/large/complex                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      3. Budget Configuration                             │
│  - Set max_sections based on bucket                                     │
│  - Set max_exploration_steps based on bucket                            │
│  - Prepare complexity context for LLM                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      4. Documentation Pipeline                           │
│  - explore_codebase() with complexity-adjusted budget                   │
│  - generate_outline() with complexity context                           │
│  - generate_sections() with adjusted per-section budget                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## Rust Complexity Analyzer

### Location
```
tools/complexity-analyzer/
├── Cargo.toml
├── src/
│   └── main.rs
└── target/
    └── release/
        └── complexity-analyzer    # Binary after build
```

### Building the Analyzer

```bash
# From project root
cd tools/complexity-analyzer

# Build release binary (optimized, ~14s first build)
cargo build --release

# Binary location
./target/release/complexity-analyzer --help
```

### Running the Analyzer

```bash
# Analyze local directory
complexity-analyzer --path /path/to/repo

# Analyze GitHub repo (clones to cache)
complexity-analyzer --repo https://github.com/owner/repo

# Output to file instead of stdout
complexity-analyzer --path /path/to/repo -o output.json
```

### Output Format

```json
{
  "repository": "repo-name",
  "scan_time_ms": 41,
  "summary": {
    "total_files": 170,
    "total_functions": 897,
    "languages": {"javascript": 164, "typescript": 6},
    "total_cyclomatic_complexity": 3353,
    "avg_cyclomatic_complexity": 3.74,
    "complexity_bucket": "simple",
    "description": "Small, focused codebase - minimal documentation needed",
    "parse_success_rate": 100.0
  },
  "distribution": {
    "low": 826,
    "medium": 60,
    "high": 11
  },
  "top_complex_functions": [
    {"file": "lib/core.js", "name": "request", "line": 45, "cyclomatic_complexity": 28, "cognitive_complexity": 45}
  ]
}
```

## Python Integration

### New Module: `tech_writer/complexity.py`

```python
"""Complexity analysis integration for proportional documentation budgets."""

import json
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Bucket thresholds (must match Rust implementation)
BUCKET_SIMPLE_MAX = 5_000
BUCKET_MEDIUM_MAX = 25_000
BUCKET_LARGE_MAX = 100_000


@dataclass
class ComplexityBudget:
    """Documentation budget derived from complexity analysis."""

    total_cc: int
    bucket: str
    max_sections: int
    max_exploration_steps: int
    section_max_steps: int
    guidance: str
    top_functions: list[dict]


def get_analyzer_path() -> Optional[Path]:
    """Find the complexity analyzer binary."""
    # Check if in PATH
    if shutil.which("complexity-analyzer"):
        return Path(shutil.which("complexity-analyzer"))

    # Check relative to this file (development setup)
    dev_path = Path(__file__).parent.parent / "tools/complexity-analyzer/target/release/complexity-analyzer"
    if dev_path.exists():
        return dev_path

    return None


def analyze_complexity(repo_path: Path) -> Optional[dict]:
    """Run complexity analyzer on a repository."""
    analyzer = get_analyzer_path()
    if not analyzer:
        return None

    try:
        result = subprocess.run(
            [str(analyzer), "--path", str(repo_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        if result.returncode != 0:
            return None

        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def map_complexity_to_budget(analysis: dict) -> ComplexityBudget:
    """Map complexity analysis to documentation budget."""
    total_cc = analysis["summary"]["total_cyclomatic_complexity"]
    top_functions = analysis.get("top_complex_functions", [])[:10]

    if total_cc < BUCKET_SIMPLE_MAX:
        return ComplexityBudget(
            total_cc=total_cc,
            bucket="simple",
            max_sections=10,
            max_exploration_steps=100,
            section_max_steps=15,
            guidance="Small, focused codebase. Cover all major components. Each section can be thorough.",
            top_functions=top_functions,
        )
    elif total_cc < BUCKET_MEDIUM_MAX:
        return ComplexityBudget(
            total_cc=total_cc,
            bucket="medium",
            max_sections=25,
            max_exploration_steps=300,
            section_max_steps=20,
            guidance="Medium codebase. Focus on architecture and key modules. Summarize peripheral code.",
            top_functions=top_functions,
        )
    elif total_cc < BUCKET_LARGE_MAX:
        return ComplexityBudget(
            total_cc=total_cc,
            bucket="large",
            max_sections=40,
            max_exploration_steps=500,
            section_max_steps=25,
            guidance="Large codebase. Prioritize core systems and complex hotspots. Use high-level summaries for stable/simple areas.",
            top_functions=top_functions,
        )
    else:
        return ComplexityBudget(
            total_cc=total_cc,
            bucket="complex",
            max_sections=50,
            max_exploration_steps=800,
            section_max_steps=30,
            guidance="Massive codebase. Focus on architecture, entry points, and the top complex functions. Cannot cover everything - prioritize what helps newcomers navigate.",
            top_functions=top_functions,
        )


def get_complexity_context(budget: ComplexityBudget) -> str:
    """Generate context string for LLM prompts."""
    hotspots = "\n".join(
        f"  - {f['file']}:{f['line']} {f['name']} (CC={f['cyclomatic_complexity']})"
        for f in budget.top_functions[:5]
    )

    return f"""## Codebase Complexity Analysis

This is a **{budget.bucket}** codebase ({budget.total_cc:,} total cyclomatic complexity).

**Documentation Strategy**: {budget.guidance}

**Complex Hotspots to Cover**:
{hotspots}

**Budget**: Up to {budget.max_sections} sections, {budget.max_exploration_steps} exploration steps.
"""
```

### Integration Points

#### 1. CLI (`tech_writer/cli.py`)

```python
from tech_writer.complexity import analyze_complexity, map_complexity_to_budget

def main():
    # ... existing arg parsing ...

    # After resolving repo path, before pipeline
    print(f"Analyzing complexity...", file=sys.stderr)
    analysis = analyze_complexity(repo_path)

    if analysis:
        budget = map_complexity_to_budget(analysis)
        print(f"Total CC: {budget.total_cc:,} ({budget.bucket})", file=sys.stderr)
        print(f"Budget: {budget.max_sections} sections, {budget.max_exploration_steps} steps", file=sys.stderr)
    else:
        print("Complexity analysis unavailable, using defaults", file=sys.stderr)
        budget = None

    # Pass budget to pipeline
    report, store, cost = run_pipeline(
        repo_path=repo_path,
        complexity_budget=budget,  # NEW parameter
        # ...
    )
```

#### 2. Orchestrator (`tech_writer/orchestrator.py`)

```python
def run_pipeline(
    repo_path: Path,
    complexity_budget: Optional[ComplexityBudget] = None,
    # ... existing params ...
) -> tuple[str, SymbolStore, float]:

    # Use complexity-derived limits or defaults
    if complexity_budget:
        max_sections = complexity_budget.max_sections
        max_exploration = complexity_budget.max_exploration_steps
        section_max_steps = complexity_budget.section_max_steps
        complexity_context = get_complexity_context(complexity_budget)
    else:
        max_sections = DEFAULT_MAX_SECTIONS
        max_exploration = DEFAULT_MAX_STEPS
        section_max_steps = DEFAULT_SECTION_MAX_STEPS
        complexity_context = ""

    # Inject complexity context into exploration prompt
    exploration_prompt = BASE_EXPLORATION_PROMPT + "\n" + complexity_context

    # ... rest of pipeline with adjusted limits ...
```

## Binary Distribution Options

### Option 1: Build on Demand (Recommended for Development)
```python
def ensure_analyzer_built() -> Path:
    """Build analyzer if not present."""
    binary = Path("tools/complexity-analyzer/target/release/complexity-analyzer")
    if not binary.exists():
        subprocess.run(
            ["cargo", "build", "--release"],
            cwd="tools/complexity-analyzer",
            check=True,
        )
    return binary
```

### Option 2: Pre-built Binary (Production)
- Build for target platforms in CI
- Include in package or download on first run
- Store in `~/.cache/tech_writer/bin/`

### Option 3: Python Fallback
- Use Python implementation if Rust unavailable
- Slower but functional
- `pocs/code-base-complexity/complexity_analyzer.py` (kept for reference/fallback)

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Rust binary not found | Log warning, use defaults |
| Analysis timeout (>5min) | Log warning, use defaults |
| Parse error in JSON | Log warning, use defaults |
| Empty repository | Return simple bucket |
| All files fail to parse | Return simple bucket with warning |

## Testing

### Unit Tests
```python
def test_bucket_mapping():
    assert map_complexity_to_budget({"summary": {"total_cyclomatic_complexity": 1000}}).bucket == "simple"
    assert map_complexity_to_budget({"summary": {"total_cyclomatic_complexity": 10000}}).bucket == "medium"
    assert map_complexity_to_budget({"summary": {"total_cyclomatic_complexity": 50000}}).bucket == "large"
    assert map_complexity_to_budget({"summary": {"total_cyclomatic_complexity": 200000}}).bucket == "complex"
```

### Integration Tests
```bash
# Build analyzer
cd pocs/code-base-complexity/rust && cargo build --release

# Test on known repos
python -m tech_writer --repo https://github.com/axios/axios --dry-run
# Should report: simple, 10 sections, 100 steps

python -m tech_writer --repo https://github.com/facebook/react --dry-run
# Should report: complex, 50 sections, 800 steps
```

## Performance Considerations

| Codebase Size | Rust Analysis Time | Acceptable? |
|---------------|-------------------|-------------|
| < 500 files | < 100ms | ✓ |
| 500-2000 files | < 1s | ✓ |
| 2000-5000 files | < 3s | ✓ |
| > 5000 files | < 10s | ✓ |

The Rust analyzer is 6-33x faster than Python. For a 4,360-file repo (React), it completes in ~2.5 seconds.
