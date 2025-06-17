#!/bin/bash
set -e -E

# Run all Gemini tool calling tests in compact mode

echo "======================================"
echo "Gemini Tool Calling Tests (Compact)"
echo "======================================"
echo ""

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY environment variable is not set"
    echo "Please set it with: export GEMINI_API_KEY='your-api-key'"
    exit 1
fi

# Make all test scripts executable
chmod +x test-*.sh

# Run each test with minimal output
tests=(
    "test-1-basic.sh"
    "test-2-complex-prompt.sh"
    "test-3-hierarchy.sh"
    "test-4-cloudflare.sh"
    "test-5-full-prompt.sh"
    "test-6-hierarchical-nav.sh"
    "test-7-subsection-validation.sh"
)

passed=0
failed=0

for test in "${tests[@]}"; do
    printf "%-30s " "$test:"
    
    if [ -f "$test" ]; then
        # Capture output and only show if test fails
        output=$(./"$test" 2>&1)
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo "✅ PASSED"
            ((passed++))
        else
            echo "❌ FAILED"
            ((failed++))
            # Show the output only for failed tests
            echo ""
            echo "--- Output from $test ---"
            echo "$output" | tail -20
            echo "--- End of output ---"
            echo ""
        fi
    else
        echo "❌ NOT FOUND"
        ((failed++))
    fi
done

echo ""
echo "======================================"
echo "Summary: $passed passed, $failed failed"
echo "======================================"

if [ $failed -eq 0 ]; then
    exit 0
else
    exit 1
fi