#!/bin/bash
# Script to create symbolic links for Python package agent makers

# Set the base directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OSS_AGENT_MAKERS_DIR="$(cd "$SCRIPT_DIR/../oss-agent-makers" && pwd)"
PYTHON_PACKAGES_DIR="$OSS_AGENT_MAKERS_DIR/python-packages"

echo "Creating Python packages view..."
echo "==============================="

# Create python-packages directory if it doesn't exist
if [ ! -d "$PYTHON_PACKAGES_DIR" ]; then
    echo "Creating directory: $PYTHON_PACKAGES_DIR"
    mkdir -p "$PYTHON_PACKAGES_DIR"
else
    # Clean up existing symlinks
    echo "Cleaning up existing symlinks..."
    find "$PYTHON_PACKAGES_DIR" -type l -delete
fi

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
        
        # Create symbolic link
        ln -s "../$dir_name" "$PYTHON_PACKAGES_DIR/$dir_name"
        echo "  Created symlink: $PYTHON_PACKAGES_DIR/$dir_name -> ../$dir_name"
    fi
done

echo ""
echo "Python packages view created!"

# Count the number of links created
link_count=$(find "$PYTHON_PACKAGES_DIR" -type l | wc -l)
echo "Total Python packages found: $link_count"