#!/bin/bash

# Generate the static HTML matrix viewer from template and data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TEMPLATE_FILE="$SCRIPT_DIR/matrix-viewer-template-with-chat.html"
MATRIX_FILE="$SCRIPT_DIR/matrix.json"
OUTPUT_FILE="$SCRIPT_DIR/matrix-viewer.html"
PROMPT_FILE="$SCRIPT_DIR/matrix.prompt.txt"

# Check if llm CLI is installed
if ! command -v llm &> /dev/null; then
    echo "Error: 'llm' CLI tool is not installed."
    echo ""
    echo "To install llm, run:"
    echo "  pip install llm"
    echo ""
    echo "Or with pipx:"
    echo "  pipx install llm"
    echo ""
    echo "Then configure your API keys:"
    echo "  llm keys set gemini"
    echo ""
    echo "For more info: https://github.com/simonw/llm"
    exit 1
fi

# Check if we're regenerating the matrix or just the HTML
REGENERATE_MATRIX=false
FORCE_REGENERATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --regenerate-matrix)
            REGENERATE_MATRIX=true
            shift
            ;;
        --force)
            FORCE_REGENERATE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--regenerate-matrix] [--force]"
            exit 1
            ;;
    esac
done

# Function to generate matrix.json using LLM
generate_matrix_json() {
    echo "Generating matrix.json using Gemini 2.0 Flash..."
    
    # Read all implementation files and create context
    IMPLEMENTATIONS=(
        "baremetal/python/tech-writer.py"
        "oss-agent-makers/adk-python/tech-writer.py"
        "oss-agent-makers/dspy/tech-writer.py"
        "oss-agent-makers/agno/tech-writer.py"
        "oss-agent-makers/langgraph/tech-writer.py"
        "oss-agent-makers/pydantic-ai/tech-writer.py"
        "oss-agent-makers/autogen/tech-writer.py"
        "oss-agent-makers/atomic-agents/tech-writer.py"
    )
    
    # Build the context with all files
    CONTEXT=""
    for impl in "${IMPLEMENTATIONS[@]}"; do
        FILE_PATH="$PROJECT_ROOT/$impl"
        if [[ -f "$FILE_PATH" ]]; then
            echo "  Reading $impl..."
            VENDOR=$(basename $(dirname "$impl"))
            if [[ "$impl" == "baremetal/python/tech-writer.py" ]]; then
                VENDOR="baremetal"
            fi
            
            CONTEXT="$CONTEXT

=== File: $impl ===
\`\`\`python
$(cat "$FILE_PATH")
\`\`\`
"
        else
            echo "  Warning: File not found: $FILE_PATH"
        fi
    done
    
    # Read the prompt
    PROMPT=$(cat "$PROMPT_FILE")
    
    # Create the full prompt with context
    FULL_PROMPT="$PROMPT

Here are all the implementation files to analyze:
$CONTEXT"
    
    # Generate the matrix using llm
    echo "  Calling Gemini 2.0 Flash to generate comparisons..."
    echo "$FULL_PROMPT" | llm -m gemini-2.0-flash-latest > "$MATRIX_FILE.tmp"
    
    # Validate the JSON
    if python3 -m json.tool "$MATRIX_FILE.tmp" > /dev/null 2>&1; then
        mv "$MATRIX_FILE.tmp" "$MATRIX_FILE"
        echo "✅ Generated matrix.json successfully"
    else
        echo "❌ Error: Generated content is not valid JSON"
        echo "Output saved to: $MATRIX_FILE.tmp"
        exit 1
    fi
}

# Check if matrix.json exists or if we should regenerate
if [[ ! -f "$MATRIX_FILE" ]] || [[ "$REGENERATE_MATRIX" == true ]]; then
    if [[ -f "$MATRIX_FILE" ]] && [[ "$FORCE_REGENERATE" != true ]]; then
        echo "matrix.json already exists. Use --force to regenerate."
        echo "Proceeding with HTML generation only..."
    else
        generate_matrix_json
    fi
fi

# Check if required files exist
if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo "Error: Template file not found: $TEMPLATE_FILE"
    exit 1
fi

if [[ ! -f "$MATRIX_FILE" ]]; then
    echo "Error: Matrix data file not found: $MATRIX_FILE"
    echo "Run with --regenerate-matrix to generate it"
    exit 1
fi

echo "Generating Tech Writer Comparison Matrix Viewer..."

# Export variables for Python
export TEMPLATE_FILE
export MATRIX_FILE
export OUTPUT_FILE
export PROJECT_ROOT

# Create a combined Python script to handle everything
python3 << 'EOF'
import json
import os
import sys

# Get paths from environment
template_file = os.environ.get('TEMPLATE_FILE')
matrix_file = os.environ.get('MATRIX_FILE')
output_file = os.environ.get('OUTPUT_FILE')
project_root = os.environ.get('PROJECT_ROOT')

# Define vendor paths
vendor_paths = {
    'baremetal': 'baremetal/python/tech-writer.py',
    'adk-python': 'oss-agent-makers/adk-python/tech-writer.py',
    'dspy': 'oss-agent-makers/dspy/tech-writer.py',
    'agno': 'oss-agent-makers/agno/tech-writer.py',
    'langgraph': 'oss-agent-makers/langgraph/tech-writer.py',
    'pydantic-ai': 'oss-agent-makers/pydantic-ai/tech-writer.py',
    'autogen': 'oss-agent-makers/autogen/tech-writer.py',
    'atomic-agents': 'oss-agent-makers/atomic-agents/tech-writer.py'
}

# Read template
print("Reading template...")
with open(template_file, 'r', encoding='utf-8') as f:
    html = f.read()

# Read matrix data
print("Reading matrix data...")
with open(matrix_file, 'r', encoding='utf-8') as f:
    matrix_data = f.read().strip()

# Read code files
print("Reading implementation files...")
code_files = {}
for vendor, path in vendor_paths.items():
    file_path = os.path.join(project_root, path)
    if os.path.exists(file_path):
        print(f"  Reading {vendor}...")
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            code_files[vendor] = f.read()
    else:
        print(f"  Warning: File not found for {vendor}: {file_path}")

# Generate properly formatted JavaScript object
code_files_js = json.dumps(code_files, indent=8, ensure_ascii=False)

# Replace placeholders
print("Building final HTML...")
html = html.replace('/* MATRIX_DATA_PLACEHOLDER */', matrix_data)
html = html.replace('/* CODE_FILES_PLACEHOLDER */', code_files_js)

# Write output
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ Generated: {output_file}")
EOF

# Make the script executable
chmod +x "$0"

echo ""
echo "To view the comparison matrix, open:"
echo "  $OUTPUT_FILE"
echo ""
echo "Or run:"
echo "  open $OUTPUT_FILE  # macOS"
echo "  xdg-open $OUTPUT_FILE  # Linux"