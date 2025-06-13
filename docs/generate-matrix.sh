#!/bin/bash

# Generate the static HTML matrix viewer from template and data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TEMPLATE_FILE="$SCRIPT_DIR/matrix-viewer-template.html"
MATRIX_FILE="$SCRIPT_DIR/matrix.json"
OUTPUT_FILE="$SCRIPT_DIR/matrix-viewer.html"

# Check if required files exist
if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo "Error: Template file not found: $TEMPLATE_FILE"
    exit 1
fi

if [[ ! -f "$MATRIX_FILE" ]]; then
    echo "Error: Matrix data file not found: $MATRIX_FILE"
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