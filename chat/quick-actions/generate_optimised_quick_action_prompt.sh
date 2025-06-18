#!/bin/bash

# Check if markdown file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <markdown_file>"
    echo "Example: $0 sources/report-with-quick-actions.md"
    exit 1
fi

MARKDOWN_FILE="$1"
BASENAME=$(basename "$MARKDOWN_FILE" .md)
OUTPUT_FILE="output/${BASENAME}.prompt.txt"

# Check if markdown file exists
if [ ! -f "$MARKDOWN_FILE" ]; then
    echo "Error: Markdown file '$MARKDOWN_FILE' not found"
    exit 1
fi

echo "Generating optimized quick action prompt for: $MARKDOWN_FILE"
echo "Output will be saved to: $OUTPUT_FILE"
echo

# Create output directory if it doesn't exist
mkdir -p output

# Step 1: Extract labels from the markdown file
echo "Step 1: Extracting training data from markdown..."

# Create a temporary Python script that accepts a custom markdown path
cat > temp_extract.py << 'EOF'
import sys
import re
import json

markdown_file = sys.argv[1]
with open(markdown_file, 'r') as f:
    content = f.read()

examples = []
for line in content.split('\n'):
    match = re.match(r'^(#{1,6})\s+(.+?)\s*\(([^)]+)\)\s*$', line)
    if match:
        examples.append({
            "level": len(match.group(1)),
            "full_heading": match.group(2).strip(),
            "short_label": match.group(3).strip(),
            "original_line": line.strip()
        })

if not examples:
    print("ERROR: No headings with parenthetical labels found.")
    print("This training program requires ground truth labels in the format:")
    print("  # Section Title (Short Label)")
    sys.exit(1)

with open('output/training_data.json', 'w') as f:
    json.dump(examples[:15], f, indent=2)

print(f"Extracted {len(examples[:15])} examples")
EOF

uv run python temp_extract.py "$MARKDOWN_FILE"

# Check if extraction was successful
if [ $? -ne 0 ]; then
    echo
    echo "Extraction failed. Exiting."
    rm -f temp_extract.py
    exit 1
fi

# Step 2: Train the model
echo
echo "Step 2: Training DSPy model..."
uv run python train_labeler.py

# Step 3: Generate the simple prompt
echo
echo "Step 3: Generating optimized prompt..."

# Generate the simple prompt using the training data
cat > temp_prompt.py << 'EOF'
import json

with open('output/training_data.json', 'r') as f:
    data = json.load(f)

examples = [f'- "{item["full_heading"]}" → "{item["short_label"]}"' for item in data[:8]]

prompt = f"""Generate a short 1-3 word label for this section heading that will be used as a quick action button.

Examples:
{chr(10).join(examples)}

Guidelines:
- Keep labels concise (1-3 words maximum)
- Use title case for labels
- For questions, extract the key topic
- For long headings, capture the essence
- Common patterns:
  - "Introduction to X" → "Introduction" or "X Intro"
  - "How to X" → "X Guide" or just "X"
  - "What is X?" → "X Overview" or just "X"
  - "X Configuration" → "X Config" or "Configuration"
  - "Getting Started with X" → "Getting Started" or "X Setup"

Heading: {{heading}}
Label:"""

print(prompt)
EOF

uv run python temp_prompt.py > "$OUTPUT_FILE"

# Cleanup
rm -f temp_extract.py temp_prompt.py

echo
echo "✅ Success! Optimized prompt saved to: $OUTPUT_FILE"

# Step 4: Test the trained model
echo
echo "Step 4: Testing the trained model..."
echo
uv run python test_labeler.py

# Step 5: Generate JavaScript implementations
echo
echo "Step 5: Generating JavaScript functions..."
echo

# Generate simple JavaScript function
echo "Generating simple JavaScript function..."
uv run python extract_prompt.py

# Generate DSPy-formatted JavaScript function
echo "Generating DSPy-formatted JavaScript function..."
uv run python extract_exact_prompt.py

echo
echo "════════════════════════════════════════════════════════════════"
echo "✅ Complete! Generated files:"
echo "════════════════════════════════════════════════════════════════"
echo "  📄 Prompt file:        $OUTPUT_FILE"
echo "  🧠 Trained model:      output/optimized_label_generator.json"
echo "  📊 Training data:      output/training_data.json"
echo "  🔧 Simple JS function: output/generateQuickActionLabel.js"
echo "  🎯 DSPy JS function:   output/generateQuickActionLabelDSPy.js"
echo "════════════════════════════════════════════════════════════════"
echo
echo "You can now:"
echo "1. Use the prompt in $OUTPUT_FILE with any LLM"
echo "2. Import the JavaScript functions in your application"
echo "3. Load the trained model for further testing"