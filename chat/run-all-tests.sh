#!/bin/bash
set -e -E

# Run all Gemini tool calling tests

echo "======================================"
echo "Running Gemini Tool Calling Test Suite"
echo "======================================"
echo ""

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY environment variable is not set"
    echo "Please set it with: export GEMINI_API_KEY='your-api-key'"
    exit 1
fi

echo "API Key is set. Starting tests..."
echo ""

# Make all test scripts executable
chmod +x test-*.sh

# Run each test with error handling
tests=(
    "test-1-basic.sh"
    "test-2-complex-prompt.sh"
    "test-3-hierarchy.sh"
    "test-4-cloudflare.sh"
    "test-5-full-prompt.sh"
)

passed=0
failed=0

for test in "${tests[@]}"; do
    echo "======================================"
    echo "Running: $test"
    echo "======================================"
    
    if [ -f "$test" ]; then
        if ./"$test"; then
            echo ""
            echo "✅ $test PASSED"
            ((passed++))
        else
            echo ""
            echo "❌ $test FAILED"
            ((failed++))
        fi
    else
        echo "❌ $test NOT FOUND"
        ((failed++))
    fi
    
    echo ""
    echo ""
done

echo "======================================"
echo "Test Summary"
echo "======================================"
echo "Total tests: ${#tests[@]}"
echo "Passed: $passed"
echo "Failed: $failed"
echo ""

if [ $failed -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi