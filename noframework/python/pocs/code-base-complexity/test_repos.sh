#!/bin/bash
# test_repos.sh - Test complexity analyzer against multiple repositories
#
# Tests both Python and Rust implementations against:
# - axios/axios (JavaScript)
# - fastapi/fastapi (Python)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=============================================="
echo "Codebase Complexity Analyzer - Test Suite"
echo "=============================================="
echo ""

# Test repositories
REPOS=(
    "https://github.com/axios/axios"
    "https://github.com/fastapi/fastapi"
)

PASSED=0
FAILED=0

for REPO in "${REPOS[@]}"; do
    REPO_NAME=$(basename "$REPO" .git)
    echo "----------------------------------------------"
    echo "Testing: ${REPO_NAME}"
    echo "----------------------------------------------"

    if "${SCRIPT_DIR}/run_comparison.sh" "$REPO"; then
        echo "✓ ${REPO_NAME}: PASSED"
        ((PASSED++))
    else
        echo "✗ ${REPO_NAME}: FAILED"
        ((FAILED++))
    fi
    echo ""
done

echo "=============================================="
echo "Test Results"
echo "=============================================="
echo "Passed: ${PASSED}"
echo "Failed: ${FAILED}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed"
    exit 1
fi
