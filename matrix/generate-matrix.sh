#!/bin/bash

# Generate the static HTML matrix viewer from template and data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TEMPLATE_FILE="$SCRIPT_DIR/matrix-viewer-template-with-chat.html"
MATRIX_FILE="$SCRIPT_DIR/matrix.json"
OUTPUT_FILE="$SCRIPT_DIR/matrix-viewer.html"
PROMPT_FILE="$SCRIPT_DIR/matrix.prompt.txt"

# Check if required tools are installed
if ! command -v jq &> /dev/null; then
    echo "Error: 'jq' is not installed."
    echo ""
    echo "To install jq:"
    echo "  macOS:    brew install jq"
    echo "  Ubuntu:   sudo apt-get install jq"
    echo "  RHEL:     sudo yum install jq"
    echo ""
    echo "For more info: https://stedolan.github.io/jq/download/"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "Error: 'curl' is not installed."
    echo "Please install curl to continue."
    exit 1
fi

# Check if we're regenerating the matrix data or just the HTML viewer
REGENERATE_DATA=false
REGENERATE_VIEWER=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --data)
            REGENERATE_DATA=true
            shift
            ;;
        --no-viewer)
            REGENERATE_VIEWER=false
            shift
            ;;
        --viewer)
            REGENERATE_VIEWER=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --data          Regenerate matrix.json data (expensive LLM calls)"
            echo "  --viewer        Generate HTML viewer (default: true)"
            echo "  --no-viewer     Skip HTML viewer generation"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Generate viewer only (default)"
            echo "  $0 --data       # Generate both data and viewer"
            echo "  $0 --data --no-viewer  # Generate data only"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to generate matrix.json using Gemini API
generate_matrix_json() {
    echo "Generating matrix.json using Gemini 2.0 Flash..."
    
    # Check for API key
    if [[ -z "$GOOGLE_API_KEY" ]]; then
        echo "Error: GOOGLE_API_KEY environment variable is not set"
        echo ""
        echo "Please set your Gemini API key:"
        echo "  export GOOGLE_API_KEY='your-api-key-here'"
        echo ""
        echo "Get your API key from: https://makersuite.google.com/app/apikey"
        exit 1
    fi
    
    # Dynamically find all tech-writer.py implementations
    IMPLEMENTATIONS=()
    
    # Add noframework implementation
    if [[ -f "$PROJECT_ROOT/noframework/python/tech-writer.py" ]]; then
        IMPLEMENTATIONS+=("noframework/python/tech-writer.py")
    fi
    
    # Find all tech-writer.py files in oss-agent-makers
    while IFS= read -r -d '' file; do
        # Get relative path from project root
        relative_path="${file#$PROJECT_ROOT/}"
        IMPLEMENTATIONS+=("$relative_path")
    done < <(find "$PROJECT_ROOT/oss-agent-makers" -name "tech-writer.py" -type f -print0 | sort -z)
    
    echo "Found ${#IMPLEMENTATIONS[@]} implementations:"
    for impl in "${IMPLEMENTATIONS[@]}"; do
        echo "  - $impl"
    done
    echo ""
    
    # Build the context with all files
    CONTEXT=""
    for impl in "${IMPLEMENTATIONS[@]}"; do
        FILE_PATH="$PROJECT_ROOT/$impl"
        if [[ -f "$FILE_PATH" ]]; then
            echo "  Reading $impl..."
            VENDOR=$(basename $(dirname "$impl"))
            if [[ "$impl" == "noframework/python/tech-writer.py" ]]; then
                VENDOR="noframework"
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
    
    # Read the prompt and tone profile
    PROMPT=$(cat "$PROMPT_FILE")
    TONE_PROFILE=""
    if [[ -f "$SCRIPT_DIR/tone-profile.txt" ]]; then
        TONE_PROFILE=$(cat "$SCRIPT_DIR/tone-profile.txt")
    fi
    
    # Create the full prompt with tone profile and context
    FULL_PROMPT="$PROMPT

$TONE_PROFILE

Here are all the implementation files to analyze:
$CONTEXT"
    
    # Create API request payload
    REQUEST_BODY=$(jq -n \
        --arg prompt "$FULL_PROMPT" \
        '{
            "contents": [{
                "parts": [{
                    "text": $prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192
            }
        }')
    
    # Call Gemini API
    echo "  Calling Gemini 2.0 Flash API..."
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "x-goog-api-key: $GOOGLE_API_KEY" \
        -d "$REQUEST_BODY" \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")
    
    # Check for API errors
    if echo "$RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
        echo "❌ API Error:"
        echo "$RESPONSE" | jq -r '.error.message'
        exit 1
    fi
    
    # Extract the generated content
    GENERATED_CONTENT=$(echo "$RESPONSE" | jq -r '.candidates[0].content.parts[0].text // empty')
    
    if [[ -z "$GENERATED_CONTENT" ]]; then
        echo "❌ Error: No content generated"
        echo "Full response saved to: matrix-api-response.json"
        echo "$RESPONSE" > "matrix-api-response.json"
        exit 1
    fi
    
    # Save to temporary file
    echo "$GENERATED_CONTENT" > "$MATRIX_FILE.tmp"
    
    # First check if the content is wrapped in markdown code blocks
    if grep -q '```json' "$MATRIX_FILE.tmp"; then
        echo "  Detected markdown-wrapped JSON, extracting..."
        # Extract content between ```json and ```
        sed -n '/^```json$/,/^```$/p' "$MATRIX_FILE.tmp" | sed '1d;$d' > "$MATRIX_FILE.tmp2"
        
        # Validate the extracted JSON
        if python3 -m json.tool "$MATRIX_FILE.tmp2" > /dev/null 2>&1; then
            mv "$MATRIX_FILE.tmp2" "$MATRIX_FILE"
            rm -f "$MATRIX_FILE.tmp"
            echo "✅ Extracted and validated JSON successfully"
        else
            echo "❌ Error: Extracted content is not valid JSON"
            echo "First few lines of extracted content:"
            head -10 "$MATRIX_FILE.tmp2"
            echo "Last few lines of extracted content:"
            tail -10 "$MATRIX_FILE.tmp2"
            rm -f "$MATRIX_FILE.tmp2"
            exit 1
        fi
    else
        # Try to validate as-is
        if python3 -m json.tool "$MATRIX_FILE.tmp" > /dev/null 2>&1; then
            mv "$MATRIX_FILE.tmp" "$MATRIX_FILE"
            echo "✅ Generated matrix.json successfully"
        else
            echo "❌ Error: Generated content is not valid JSON"
            echo "First few lines of response:"
            head -10 "$MATRIX_FILE.tmp"
            echo "Last few lines of response:"
            tail -10 "$MATRIX_FILE.tmp"
            exit 1
        fi
    fi
}

# Check if we should regenerate matrix data
if [[ "$REGENERATE_DATA" == true ]]; then
    generate_matrix_json
elif [[ ! -f "$MATRIX_FILE" ]]; then
    echo "Error: matrix.json not found. Run with --data to generate it."
    exit 1
fi

# Exit early if we're not generating the viewer
if [[ "$REGENERATE_VIEWER" == false ]]; then
    echo "Skipping HTML viewer generation (--no-viewer specified)"
    exit 0
fi

# Check if required files exist
if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo "Error: Template file not found: $TEMPLATE_FILE"
    exit 1
fi

if [[ ! -f "$MATRIX_FILE" ]]; then
    echo "Error: Matrix data file not found: $MATRIX_FILE"
    echo "Run with --data to generate it"
    exit 1
fi

echo "Generating Tech Writer Comparison Matrix Viewer..."

# Function to find all tech-writer.py implementations
find_implementations() {
    local implementations=()
    
    # Add noframework if it exists
    if [[ -f "$PROJECT_ROOT/noframework/python/tech-writer.py" ]]; then
        implementations+=("noframework:noframework/python/tech-writer.py")
    fi
    
    # Find all tech-writer.py files in oss-agent-makers
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            local vendor=$(basename $(dirname "$file"))
            local relative_path="${file#$PROJECT_ROOT/}"
            implementations+=("${vendor}:${relative_path}")
        fi
    done < <(find "$PROJECT_ROOT/oss-agent-makers" -name "tech-writer.py" -type f | sort)
    
    printf '%s\n' "${implementations[@]}"
}

# Find all implementations
IMPLEMENTATIONS=($(find_implementations))
echo "Found ${#IMPLEMENTATIONS[@]} implementations:"
for impl in "${IMPLEMENTATIONS[@]}"; do
    vendor="${impl%%:*}"
    path="${impl#*:}"
    echo "  ${vendor}: ${path}"
done

# Read template
echo "Reading template..."
TEMPLATE_CONTENT=$(<"$TEMPLATE_FILE")

# Read matrix data
echo "Reading matrix data..."
MATRIX_DATA=$(<"$MATRIX_FILE")

# Read tone profile
echo "Reading tone profile..."
TONE_PROFILE=""
if [[ -f "$SCRIPT_DIR/tone-profile.txt" ]]; then
    TONE_PROFILE=$(<"$SCRIPT_DIR/tone-profile.txt")
fi

# Read code files and build JSON object
echo "Reading implementation files..."
CODE_FILES_JSON="{"
first=true
for impl in "${IMPLEMENTATIONS[@]}"; do
    vendor="${impl%%:*}"
    path="${impl#*:}"
    file_path="$PROJECT_ROOT/$path"
    
    if [[ -f "$file_path" ]]; then
        echo "  Reading ${vendor}..."
        
        # Add comma if not first entry
        if [[ "$first" == false ]]; then
            CODE_FILES_JSON+=","
        fi
        first=false
        
        # Read file content and escape for JSON
        file_content=$(<"$file_path")
        # Escape backslashes, quotes, and newlines for JSON
        escaped_content=$(echo "$file_content" | jq -Rs .)
        
        # Add to JSON object
        CODE_FILES_JSON+=$'\n'"        \"${vendor}\": ${escaped_content}"
    else
        echo "  Warning: File not found for ${vendor}: ${file_path}"
    fi
done
CODE_FILES_JSON+=$'\n'"}"

# Replace placeholders in template
echo "Building final HTML..."

# Create temporary files for the data
MATRIX_TMP=$(mktemp)
CODE_TMP=$(mktemp)
TONE_TMP=$(mktemp)
echo "$MATRIX_DATA" > "$MATRIX_TMP"
echo "$CODE_FILES_JSON" > "$CODE_TMP"
echo "$TONE_PROFILE" > "$TONE_TMP"

# Process template line by line
while IFS= read -r line || [ -n "$line" ]; do
    if [[ "$line" == *"/* MATRIX_DATA_PLACEHOLDER */"* ]]; then
        # Replace the placeholder with the actual data
        echo "${line/\/\* MATRIX_DATA_PLACEHOLDER \*\//$(<"$MATRIX_TMP")}"
    elif [[ "$line" == *"/* CODE_FILES_PLACEHOLDER */"* ]]; then
        # Replace the placeholder with the actual data
        echo "${line/\/\* CODE_FILES_PLACEHOLDER \*\//$(<"$CODE_TMP")}"
    elif [[ "$line" == *"/* TONE_PROFILE_PLACEHOLDER */"* ]]; then
        # Replace the placeholder with the tone profile
        echo "${line/\/\* TONE_PROFILE_PLACEHOLDER \*\//$(<"$TONE_TMP")}"
    else
        echo "$line"
    fi
done < "$TEMPLATE_FILE" > "$OUTPUT_FILE"

# Clean up temporary files
rm -f "$MATRIX_TMP" "$CODE_TMP" "$TONE_TMP"

echo "✅ Generated: $OUTPUT_FILE"

# Make the script executable
chmod +x "$0"

echo ""
echo "To view the comparison matrix, open:"
echo "  $OUTPUT_FILE"
echo ""
echo "Or run:"
echo "  open $OUTPUT_FILE  # macOS"
echo "  xdg-open $OUTPUT_FILE  # Linux"