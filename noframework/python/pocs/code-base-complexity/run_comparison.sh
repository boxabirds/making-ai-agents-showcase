#!/bin/bash
# run_comparison.sh - Compare Python and Rust complexity analyzer outputs
#
# Usage: ./run_comparison.sh <repo_url_or_path>
# Example: ./run_comparison.sh https://github.com/axios/axios

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/output"

if [ -z "$1" ]; then
    echo "Usage: $0 <repo_url_or_path>"
    echo "Example: $0 https://github.com/axios/axios"
    echo "Example: $0 /path/to/local/repo"
    exit 1
fi

INPUT="$1"
mkdir -p "${OUTPUT_DIR}"

# Determine if input is URL or path
if [[ "$INPUT" == http* ]]; then
    REPO_NAME=$(basename "$INPUT" .git)
    ARG_TYPE="--repo"
else
    REPO_NAME=$(basename "$INPUT")
    ARG_TYPE="--path"
fi

PYTHON_OUTPUT="${OUTPUT_DIR}/${REPO_NAME}_python.json"
RUST_OUTPUT="${OUTPUT_DIR}/${REPO_NAME}_rust.json"

echo "=========================================="
echo "Comparing Python vs Rust implementations"
echo "Repository: ${INPUT}"
echo "=========================================="
echo ""

# Run Python implementation
echo "Running Python implementation..."
PYTHON_START=$(python3 -c 'import time; print(int(time.time()*1000))')
python3 "${SCRIPT_DIR}/complexity_analyzer.py" ${ARG_TYPE} "${INPUT}" -o "${PYTHON_OUTPUT}"
PYTHON_END=$(python3 -c 'import time; print(int(time.time()*1000))')
PYTHON_TIME=$((PYTHON_END - PYTHON_START))
echo "Python completed in ${PYTHON_TIME}ms"
echo ""

# Build and run Rust implementation
echo "Building Rust implementation..."
(cd "${SCRIPT_DIR}/rust" && cargo build --release --quiet)

echo "Running Rust implementation..."
RUST_START=$(python3 -c 'import time; print(int(time.time()*1000))')
"${SCRIPT_DIR}/rust/target/release/complexity-analyzer" ${ARG_TYPE} "${INPUT}" -o "${RUST_OUTPUT}"
RUST_END=$(python3 -c 'import time; print(int(time.time()*1000))')
RUST_TIME=$((RUST_END - RUST_START))
echo "Rust completed in ${RUST_TIME}ms"
echo ""

# Compare outputs
echo "=========================================="
echo "Comparison Results"
echo "=========================================="
echo ""

# Extract key metrics using Python
python3 << EOF
import json
import sys

def load_json(path):
    with open(path) as f:
        return json.load(f)

py = load_json("${PYTHON_OUTPUT}")
rs = load_json("${RUST_OUTPUT}")

def compare(name, py_val, rs_val, tolerance=0.01):
    if isinstance(py_val, float) and isinstance(rs_val, float):
        diff = abs(py_val - rs_val)
        match = diff <= tolerance * max(abs(py_val), abs(rs_val), 1)
        status = "✓" if match else "✗"
        print(f"  {name}: Python={py_val:.2f}, Rust={rs_val:.2f} {status}")
    else:
        match = py_val == rs_val
        status = "✓" if match else "✗"
        print(f"  {name}: Python={py_val}, Rust={rs_val} {status}")
    return match

print("Summary Comparison:")
matches = []
matches.append(compare("Total files", py["summary"]["total_files"], rs["summary"]["total_files"]))
matches.append(compare("Total functions", py["summary"]["total_functions"], rs["summary"]["total_functions"]))
matches.append(compare("Complexity score", py["summary"]["complexity_score"], rs["summary"]["complexity_score"], 0.05))
matches.append(compare("Complexity bucket", py["summary"]["complexity_bucket"], rs["summary"]["complexity_bucket"]))
print()

print("Distribution Comparison:")
matches.append(compare("Low complexity", py["distribution"]["low"], rs["distribution"]["low"]))
matches.append(compare("Medium complexity", py["distribution"]["medium"], rs["distribution"]["medium"]))
matches.append(compare("High complexity", py["distribution"]["high"], rs["distribution"]["high"]))
print()

print("Language Breakdown:")
py_langs = py["summary"]["languages"]
rs_langs = rs["summary"]["languages"]
all_langs = set(py_langs.keys()) | set(rs_langs.keys())
for lang in sorted(all_langs):
    py_count = py_langs.get(lang, 0)
    rs_count = rs_langs.get(lang, 0)
    matches.append(compare(f"  {lang}", py_count, rs_count))
print()

print("Top Complex Functions (Top 5):")
py_top = py.get("top_complex_functions", [])[:5]
rs_top = rs.get("top_complex_functions", [])[:5]
for i, (pf, rf) in enumerate(zip(py_top, rs_top)):
    py_name = f"{pf['file']}:{pf['name']}"
    rs_name = f"{rf['file']}:{rf['name']}"
    name_match = pf['name'] == rf['name']
    cc_match = pf['cyclomatic_complexity'] == rf['cyclomatic_complexity']
    status = "✓" if (name_match and cc_match) else "✗"
    print(f"  #{i+1} Python: {pf['name']} (CC={pf['cyclomatic_complexity']})")
    print(f"      Rust:   {rf['name']} (CC={rf['cyclomatic_complexity']}) {status}")
    matches.append(name_match and cc_match)
print()

print("========================================")
passed = sum(matches)
total = len(matches)
print(f"Total: {passed}/{total} checks passed")
if passed == total:
    print("✓ All checks passed!")
    sys.exit(0)
else:
    print("✗ Some checks failed")
    sys.exit(1)
EOF

echo ""
echo "=========================================="
echo "Performance Comparison"
echo "=========================================="
echo "Python: ${PYTHON_TIME}ms"
echo "Rust:   ${RUST_TIME}ms"

if [ "$RUST_TIME" -gt 0 ]; then
    SPEEDUP=$(python3 -c "print(f'{${PYTHON_TIME} / ${RUST_TIME}:.2f}x')")
    echo "Rust speedup: ${SPEEDUP}"
fi
echo ""

echo "Output files:"
echo "  Python: ${PYTHON_OUTPUT}"
echo "  Rust:   ${RUST_OUTPUT}"
