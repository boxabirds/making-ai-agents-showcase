#!/bin/bash
# Script to organize output files by repository name

# Set the base directory (parent of setup)
SETUP_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(cd "$SETUP_DIR/../oss-agent-makers" && pwd)"
OUTPUT_DIR="$SETUP_DIR/output"

# Check if output directory exists
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: Output directory not found: $OUTPUT_DIR"
    exit 1
fi

echo "Organizing output files..."
echo "=========================="

# Process each metadata.json file
for metadata_file in "$OUTPUT_DIR"/*.metadata.json; do
    # Skip if no metadata files found
    [ ! -f "$metadata_file" ] && continue
    
    # Get the base name (stem) of the file
    base_name=$(basename "$metadata_file" .metadata.json)
    
    # Extract repo_name from metadata
    repo_name=$(python3 -c "
import json
with open('$metadata_file', 'r') as f:
    data = json.load(f)
    print(data.get('repo_name', ''))
" 2>/dev/null)
    
    # Skip if repo_name is empty
    if [ -z "$repo_name" ]; then
        echo "Warning: No repo_name found in $metadata_file, skipping..."
        continue
    fi
    
    # Look for corresponding .sh file
    sh_file="$OUTPUT_DIR/${base_name}.sh"
    
    if [ ! -f "$sh_file" ]; then
        echo "Warning: No matching .sh file found for $metadata_file, skipping..."
        continue
    fi
    
    # Create repository directory if it doesn't exist
    repo_dir="$BASE_DIR/$repo_name"
    if [ ! -d "$repo_dir" ]; then
        echo "Creating directory: $repo_dir"
        mkdir -p "$repo_dir"
    fi
    
    # Move files
    echo "Processing $repo_name:"
    echo "  Moving $metadata_file -> $repo_dir/metadata.json"
    mv "$metadata_file" "$repo_dir/metadata.json"
    
    echo "  Moving $sh_file -> $repo_dir/install.sh"
    mv "$sh_file" "$repo_dir/install.sh"
    chmod +x "$repo_dir/install.sh"
    
    echo "  Done."
    echo ""
done

echo "Organization complete!"

# Check if any files remain in output directory
remaining_files=$(ls "$OUTPUT_DIR"/*.{sh,metadata.json} 2>/dev/null | wc -l)
if [ $remaining_files -gt 0 ]; then
    echo ""
    echo "Warning: Some files could not be processed and remain in $OUTPUT_DIR"
fi