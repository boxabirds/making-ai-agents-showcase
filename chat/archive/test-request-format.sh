#!/bin/bash
set -e -E

# Test request format validation
echo "=== Request Format Validation ==="
echo "This script validates the JSON request format for each test"
echo ""

tests=(
    "test-1-basic.sh"
    "test-2-complex-prompt.sh"
    "test-3-hierarchy.sh"
    "test-4-cloudflare.sh"
    "test-5-full-prompt.sh"
    "test-6-hierarchical-nav.sh"
)

for test in "${tests[@]}"; do
    echo "Checking $test..."
    
    # Extract JSON from test file
    # Look for the first cat << EOF > request.json block
    awk '/^cat << EOF > request\.json$/,/^EOF$/' "$test" | sed '1d;$d' | head -n 100 > temp_request.json
    
    # Validate JSON
    if jq empty temp_request.json 2>/dev/null; then
        echo "✅ Valid JSON"
        
        # Check for required fields
        echo -n "  - Contents: "
        if jq -e '.contents' temp_request.json >/dev/null 2>&1; then
            echo "✅"
        else
            echo "❌ Missing"
        fi
        
        echo -n "  - Tools: "
        if jq -e '.tools' temp_request.json >/dev/null 2>&1; then
            echo "✅"
            # Check tool structure
            echo -n "  - Function declarations: "
            if jq -e '.tools[0].functionDeclarations' temp_request.json >/dev/null 2>&1; then
                echo "✅"
                # Show function names
                functions=$(jq -r '.tools[0].functionDeclarations[].name' temp_request.json 2>/dev/null)
                echo "    Functions: $functions"
            else
                echo "❌ Missing"
            fi
        else
            echo "❌ Missing"
        fi
        
        echo -n "  - Generation config: "
        if jq -e '.generationConfig' temp_request.json >/dev/null 2>&1; then
            echo "✅"
        else
            echo "❌ Missing"
        fi
    else
        echo "❌ Invalid JSON"
    fi
    
    echo ""
done

rm -f temp_request.json

echo "Done!"