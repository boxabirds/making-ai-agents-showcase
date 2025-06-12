#!/bin/bash

# Tech Writer Evaluation Script
# Tests a specific tech writer implementation to ensure it works to spec

set -euo pipefail

# Check if script path is provided
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <tech-writer-script-path>"
    echo "Example: $0 ../baremetal/python/tech-writer.sh"
    echo "Example: $0 ../baremetal/bash/tech-writer.sh"
    exit 1
fi

SCRIPT_PATH="$1"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EVAL_OUTPUT_DIR="${SCRIPT_DIR}/output"
EVAL_PROMPT="${SCRIPT_DIR}/eval.prompt.txt"
TEST_REPO="https://github.com/axios/axios"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
MODEL="${MODEL:-openai/gpt-4o-mini}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$EVAL_OUTPUT_DIR"

# Extract implementation name from script path
IMPL_NAME=$(basename "$(dirname "$SCRIPT_PATH")")

# Logging
LOG_FILE="${EVAL_OUTPUT_DIR}/eval-${IMPL_NAME}-${TIMESTAMP}.log"
echo "Tech Writer Evaluation - $(date)" | tee "$LOG_FILE"
echo "=======================================" | tee -a "$LOG_FILE"
echo "Implementation: $IMPL_NAME" | tee -a "$LOG_FILE"
echo "Script: $SCRIPT_PATH" | tee -a "$LOG_FILE"
echo "Test Repository: $TEST_REPO" | tee -a "$LOG_FILE"
echo "Model: $MODEL" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check prerequisites
check_prerequisites() {
    local missing=()
    
    # Check for required environment variables
    if [[ -z "${OPENAI_API_KEY:-}" ]] && [[ -z "${GEMINI_API_KEY:-}" ]]; then
        echo -e "${RED}ERROR: No API keys found. Set OPENAI_API_KEY or GEMINI_API_KEY${NC}" | tee -a "$LOG_FILE"
        exit 1
    fi
    
    # Check for eval prompt
    if [[ ! -f "$EVAL_PROMPT" ]]; then
        echo -e "${RED}ERROR: Evaluation prompt not found: $EVAL_PROMPT${NC}" | tee -a "$LOG_FILE"
        exit 1
    fi
    
    # Check for required commands
    command -v jq >/dev/null 2>&1 || missing+=("jq")
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${RED}ERROR: Missing required commands: ${missing[*]}${NC}" | tee -a "$LOG_FILE"
        echo "Please install them first." | tee -a "$LOG_FILE"
        exit 1
    fi
}

# Test a single tech writer implementation
test_tech_writer() {
    local name="$1"
    local script_path="$2"
    
    echo -e "\n${BLUE}Testing: $name${NC}" | tee -a "$LOG_FILE"
    echo "Script: $script_path" | tee -a "$LOG_FILE"
    
    # Check if script exists
    if [[ ! -f "$script_path" ]]; then
        echo -e "${RED}✗ Script not found${NC}" | tee -a "$LOG_FILE"
        return 1
    fi
    
    # Make sure it's executable
    if [[ ! -x "$script_path" ]]; then
        chmod +x "$script_path" 2>/dev/null || true
    fi
    
    # Prepare output filename
    local output_file="${EVAL_OUTPUT_DIR}/eval-${name}-${TIMESTAMP}.md"
    
    # Build command - all implementations should use --prompt
    local cmd="$script_path --repo '$TEST_REPO' --prompt '$EVAL_PROMPT' --output-dir '$EVAL_OUTPUT_DIR' --file-name '$(basename "$output_file")' --model '$MODEL'"
    
    echo "Command: $cmd" | tee -a "$LOG_FILE"
    
    # Run the command with timeout
    local start_time=$(date +%s)
    local exit_code=0
    
    if timeout 300 bash -c "cd '$(dirname "$script_path")' && ./$(basename "$script_path") ${cmd#*$script_path}" >> "$LOG_FILE" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        # Check if output file was created
        if [[ -f "$output_file" ]]; then
            local file_size=$(wc -c < "$output_file" | tr -d ' ')
            if [[ $file_size -gt 100 ]]; then
                echo -e "${GREEN}✓ Success${NC} - Generated $(wc -l < "$output_file" | tr -d ' ') lines in ${duration}s" | tee -a "$LOG_FILE"
                
                # Extract first few lines for preview
                echo "Preview:" | tee -a "$LOG_FILE"
                head -5 "$output_file" | sed 's/^/  /' | tee -a "$LOG_FILE"
                echo "  ..." | tee -a "$LOG_FILE"
                
                return 0
            else
                echo -e "${RED}✗ Failed${NC} - Output file too small (${file_size} bytes)" | tee -a "$LOG_FILE"
                return 1
            fi
        else
            echo -e "${RED}✗ Failed${NC} - No output file created" | tee -a "$LOG_FILE"
            return 1
        fi
    else
        exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            echo -e "${RED}✗ Failed${NC} - Timeout after 300s" | tee -a "$LOG_FILE"
        else
            echo -e "${RED}✗ Failed${NC} - Exit code: $exit_code" | tee -a "$LOG_FILE"
        fi
        return 1
    fi
}

# Main evaluation
main() {
    check_prerequisites
    
    # Check if script exists
    if [[ ! -f "$SCRIPT_PATH" ]]; then
        echo -e "${RED}ERROR: Script not found: $SCRIPT_PATH${NC}" | tee -a "$LOG_FILE"
        exit 1
    fi
    
    echo -e "\n${YELLOW}Starting Tech Writer Evaluation${NC}" | tee -a "$LOG_FILE"
    echo "=======================================" | tee -a "$LOG_FILE"
    
    # Test the implementation
    if test_tech_writer "$IMPL_NAME" "$SCRIPT_PATH"; then
        echo -e "\n${GREEN}Test passed!${NC}" | tee -a "$LOG_FILE"
        exit 0
    else
        echo -e "\n${RED}Test failed.${NC}" | tee -a "$LOG_FILE"
        exit 1
    fi
}

# Run main
main "$@"