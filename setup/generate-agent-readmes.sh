#!/bin/bash

# Script to generate READMEs for all agent implementations
# Goes through every folder in oss-agent-makers/python-packages/
# Reads metadata.json to get repo_url
# Runs tech-writer.sh to generate README

# Check for required dependencies
if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed."
    echo "jq is required to parse JSON files."
    echo ""
    echo "To install jq:"
    echo "  - On macOS: brew install jq"
    echo "  - On Ubuntu/Debian: sudo apt-get install jq"
    echo "  - On CentOS/RHEL: sudo yum install jq"
    echo ""
    exit 1
fi

# Base directories
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
AGENTS_DIR="$BASE_DIR/oss-agent-makers/python-packages"
TECH_WRITER_SCRIPT="$BASE_DIR/noframework/python/tech-writer.sh"
PROMPT_FILE="$BASE_DIR/noframework/python/prompts/get-api-summary.prompt.txt"

# Check if required directories and files exist
if [ ! -d "$AGENTS_DIR" ]; then
    echo "Error: Agent packages directory not found at $AGENTS_DIR"
    exit 1
fi

if [ ! -f "$TECH_WRITER_SCRIPT" ]; then
    echo "Error: tech-writer.sh not found at $TECH_WRITER_SCRIPT"
    exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: Prompt file not found at $PROMPT_FILE"
    exit 1
fi

# Change to noframework/python directory for running tech-writer.sh
cd "$BASE_DIR/noframework/python"

# Counter for processed agents
processed=0
skipped=0

echo "Starting README generation for agent implementations..."
echo "==========================================="

# Iterate through each agent folder
for agent_dir in "$AGENTS_DIR"/*; do
    if [ -d "$agent_dir" ]; then
        agent_name=$(basename "$agent_dir")
        metadata_file="$agent_dir/metadata.json"
        
        echo ""
        echo "Processing: $agent_name"
        echo "-----------"
        
        # Check if README.md already exists
        if [ -f "$agent_dir/README.md" ]; then
            echo "ℹ️  README.md already exists in $agent_name, skipping..."
            ((skipped++))
            continue
        fi
        
        # Check if metadata.json exists
        if [ ! -f "$metadata_file" ]; then
            echo "⚠️  Warning: metadata.json not found in $agent_name, skipping..."
            ((skipped++))
            continue
        fi
        
        # Extract github_url from metadata.json
        github_url=$(jq -r '.github_url // empty' "$metadata_file" 2>/dev/null)
        
        if [ -z "$github_url" ] || [ "$github_url" = "null" ]; then
            echo "⚠️  Warning: github_url not found in metadata.json for $agent_name, skipping..."
            ((skipped++))
            continue
        fi
        
        echo "Found repo URL: $github_url"
        
        # Output file path
        output_file="$agent_dir/README.md"
        
        # Run tech-writer.sh
        echo "Running tech-writer.sh..."
        if ./tech-writer.sh --repo "$github_url" --prompt "$PROMPT_FILE" --output-dir "$agent_dir" --file-name "README.md"; then
            echo "✅ Successfully generated README for $agent_name"
            ((processed++))
        else
            echo "❌ Failed to generate README for $agent_name"
            ((skipped++))
        fi
    fi
done

echo ""
echo "==========================================="
echo "README generation complete!"
echo "Processed: $processed agents"
echo "Skipped: $skipped agents"
echo "Total: $((processed + skipped)) agents"