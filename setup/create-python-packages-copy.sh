#!/bin/bash
# Script to copy Python package agent makers to a dedicated directory

# Set the base directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OSS_AGENT_MAKERS_DIR="$(cd "$SCRIPT_DIR/../oss-agent-makers" && pwd)"
PYTHON_PACKAGES_DIR="$OSS_AGENT_MAKERS_DIR/python-packages"

echo "Copying Python package agent makers..."
echo "====================================="

# Create python-packages directory if it doesn't exist
if [ ! -d "$PYTHON_PACKAGES_DIR" ]; then
    echo "Creating directory: $PYTHON_PACKAGES_DIR"
    mkdir -p "$PYTHON_PACKAGES_DIR"
else
    # Clean up existing directories (except README.md if it exists)
    echo "Cleaning up existing directories..."
    find "$PYTHON_PACKAGES_DIR" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
fi

# Track count
count=0

# Process each directory in oss-agent-makers
for dir in "$OSS_AGENT_MAKERS_DIR"/*/; do
    # Skip if not a directory
    [ ! -d "$dir" ] && continue
    
    # Get directory name
    dir_name=$(basename "$dir")
    
    # Skip the python-packages directory itself
    if [ "$dir_name" == "python-packages" ]; then
        continue
    fi
    
    # Check if metadata.json exists
    metadata_file="$dir/metadata.json"
    if [ ! -f "$metadata_file" ]; then
        continue
    fi
    
    # Extract eval_output from metadata.json
    eval_output=$(python3 -c "
import json
try:
    with open('$metadata_file', 'r') as f:
        data = json.load(f)
        print(data.get('eval_output', ''))
except:
    print('')
" 2>/dev/null)
    
    # Check if it's "Package option, Python"
    if [ "$eval_output" == "Package option, Python" ]; then
        echo "Found Python package: $dir_name"
        
        # Copy the directory
        cp -r "$dir" "$PYTHON_PACKAGES_DIR/$dir_name"
        echo "  Copied to: $PYTHON_PACKAGES_DIR/$dir_name"
        ((count++))
    fi
done

echo ""
echo "Python packages copied!"
echo "Total Python packages found: $count"