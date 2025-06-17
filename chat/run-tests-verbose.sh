#!/bin/bash
set -e -E

# Run specific test with extra verbose output

if [ -z "$1" ]; then
    echo "Usage: ./run-tests-verbose.sh <test-file>"
    echo "Example: ./run-tests-verbose.sh test-6-hierarchical-nav.sh"
    exit 1
fi

TEST_FILE="$1"

if [ ! -f "$TEST_FILE" ]; then
    echo "Error: Test file '$TEST_FILE' not found"
    exit 1
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY environment variable is not set"
    echo "Please set it with: export GEMINI_API_KEY='your-api-key'"
    exit 1
fi

echo "======================================"
echo "Running $TEST_FILE with verbose output"
echo "======================================"
echo ""

# Run with verbose curl output
export VERBOSE=1

# Replace curl command to add -v flag
sed 's/curl -s/curl -v/g' "$TEST_FILE" > temp_verbose_test.sh
chmod +x temp_verbose_test.sh

# Run the verbose version
./temp_verbose_test.sh

# Cleanup
rm -f temp_verbose_test.sh