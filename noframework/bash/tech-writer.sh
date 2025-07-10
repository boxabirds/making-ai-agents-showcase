#!/bin/bash

# Tech Writer Agent - Pure Bash Implementation
# A complete bash port of the Python tech writer agent with all common functionality included

set -euo pipefail

# Constants
readonly TEMPERATURE=0

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${HOME}/.cache/github"
OUTPUT_DIR="output"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE=""
MODEL="openai/gpt-4o-mini"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
GEMINI_API_KEY="${GEMINI_API_KEY:-}"
BASE_URL=""
MAX_STEPS=50
MEMORY=()
FINAL_ANSWER=""

# ANSI color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# React system prompt (matching Python version)
REACT_SYSTEM_PROMPT="You are a technical documentation assistant that analyses codebases and generates comprehensive documentation.

When given a directory path and a specific analysis request, you will:
1. Explore the codebase structure to understand its organization
2. Read relevant files to comprehend the implementation details
3. Generate detailed technical documentation based on your analysis

You have access to tools that help you explore and understand codebases:
- find_all_matching_files: Find files matching patterns in directories
- read_file: Read the contents of specific files

Important guidelines:
- Always start by exploring the directory structure to understand the codebase layout
- Read files strategically based on the documentation needs
- Pay attention to configuration files, main entry points, and key modules
- Generate clear, well-structured documentation that would help developers understand the codebase

Use the following format:

Thought: I need to [describe what you need to do next]
Action: [tool_name]
Action Input: {\"param1\": \"value1\", \"param2\": \"value2\"}
Observation: [tool output will be provided here]
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have enough information to generate the documentation
Final Answer: [Your complete technical documentation]

Begin your analysis now."

# Check dependencies
check_dependencies() {
    local missing=()
    
    command -v jq >/dev/null 2>&1 || missing+=("jq")
    command -v curl >/dev/null 2>&1 || missing+=("curl")
    command -v git >/dev/null 2>&1 || missing+=("git")
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Error: Missing required dependencies: ${missing[*]}" >&2
        echo "Please install them first:" >&2
        echo "  macOS: brew install ${missing[*]}" >&2
        echo "  Ubuntu/Debian: sudo apt-get install ${missing[*]}" >&2
        exit 1
    fi
}

# Logging functions
log_init() {
    mkdir -p "$LOG_DIR"
    local timestamp=$(date +"%Y%m%d-%H%M%S")
    LOG_FILE="${LOG_DIR}/tech-writer-${timestamp}.log"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - Logging to file: $LOG_FILE" | tee "$LOG_FILE"
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${timestamp} - ${level} - ${message}" | tee -a "$LOG_FILE" >&2
}

log_info() {
    log "INFO" "$@"
}

log_error() {
    log "ERROR" "$@"
}

log_debug() {
    log "DEBUG" "$@"
}

# Utility functions
sanitize_filename() {
    local name="$1"
    # Replace unsafe characters with hyphens
    echo "$name" | tr '/\\:*?"<>|' '---------'
}

# JSON escape function using jq
json_escape() {
    local text="$1"
    # Use jq to properly escape JSON strings
    echo -n "$text" | jq -Rs '.'
}

# JSON string escape (for building JSON manually)
json_string() {
    local text="$1"
    # Escape special characters for JSON
    echo -n "$text" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed 's/	/\\t/g' | tr '\n' '\r' | sed 's/\r/\\n/g'
}

# Tool: find_all_matching_files
find_all_matching_files() {
    local directory="$1"
    local pattern="${2:-*}"
    local respect_gitignore="${3:-true}"
    local include_hidden="${4:-false}"
    local include_subdirs="${5:-true}"
    
    log_info "Tool invoked: find_all_matching_files(directory='$directory', pattern='$pattern', respect_gitignore=$respect_gitignore, include_hidden=$include_hidden, include_subdirs=$include_subdirs)"
    
    if [[ ! -d "$directory" ]]; then
        log_error "Directory not found: $directory"
        echo "[]"
        return
    fi
    
    local find_cmd="find"
    local find_opts=()
    
    # Convert to absolute path
    directory=$(cd "$directory" && pwd)
    
    find_opts+=("$directory")
    
    # Handle subdirectories
    if [[ "$include_subdirs" != "true" ]]; then
        find_opts+=("-maxdepth" "1")
    fi
    
    # Always exclude .git directory first
    find_opts+=("-path" "*/.git" "-prune" "-o")
    
    # Handle hidden files
    if [[ "$include_hidden" != "true" ]]; then
        # Exclude hidden files and directories (but not hidden files in root)
        find_opts+=("-name" ".*" "-prune" "-o")
    fi
    
    # Add file type and pattern
    find_opts+=("-type" "f")
    
    # Handle patterns
    if [[ "$pattern" != "*.*" ]] && [[ "$pattern" != "*" ]]; then
        find_opts+=("-name" "$pattern")
    fi
    
    # Print the results
    find_opts+=("-print")
    
    # Execute find and process results
    log_debug "Find command: $find_cmd ${find_opts[@]}"
    local results="["
    local first=true
    
    while IFS= read -r file; do
        # Skip if gitignore should be respected and file is ignored
        if [[ "$respect_gitignore" == "true" ]] && command -v git >/dev/null 2>&1; then
            # Check if the directory is a git repository
            if [[ -d "$directory/.git" ]] && git -C "$directory" check-ignore "$file" 2>/dev/null; then
                continue
            fi
        fi
        
        if [[ "$first" == "true" ]]; then
            first=false
        else
            results+=","
        fi
        results+="\"$(json_string "$file")\""
    done < <($find_cmd "${find_opts[@]}" 2>/dev/null || true)
    
    results+="]"
    echo "$results"
    
    local count=$(echo "$results" | jq 'length')
    log_info "Found $count matching files"
}

# Tool: read_file
read_file() {
    local file_path="$1"
    
    log_info "Tool invoked: read_file(file_path='$file_path')"
    
    if [[ ! -f "$file_path" ]]; then
        echo "{\"error\": \"File not found: $file_path\"}"
        return
    fi
    
    # Check if file is binary
    if file -b --mime-encoding "$file_path" | grep -q binary; then
        log_debug "File detected as binary: $file_path"
        echo "{\"error\": \"Cannot read binary file: $file_path\"}"
        return
    fi
    
    # Read file content
    local content
    if content=$(cat "$file_path" 2>/dev/null); then
        local char_count=${#content}
        log_info "Successfully read file: $file_path ($char_count chars)"
        
        # Build JSON response
        echo "{\"file\": \"$(json_string "$file_path")\", \"content\": \"$(json_string "$content")\"}"
    else
        echo "{\"error\": \"Failed to read file: $file_path\"}"
    fi
}

# OpenAI API call function
call_openai_api() {
    local messages="$1"
    local vendor="${MODEL%%/*}"
    local model_id="${MODEL#*/}"
    local api_key=""
    local api_url=""
    
    # Determine API endpoint and key based on vendor
    if [[ "$vendor" == "google" ]]; then
        api_key="$GEMINI_API_KEY"
        api_url="${BASE_URL:-https://generativelanguage.googleapis.com/v1beta/openai/chat/completions}"
    elif [[ "$vendor" == "openai" ]]; then
        api_key="$OPENAI_API_KEY"
        api_url="${BASE_URL:-https://api.openai.com/v1/chat/completions}"
    else
        log_error "Unknown model vendor: $vendor"
        return 1
    fi
    
    if [[ -z "$api_key" ]]; then
        log_error "API key not set for vendor: $vendor"
        return 1
    fi
    
    # Prepare the request
    local request_body=$(jq -n \
        --arg model "$model_id" \
        --argjson messages "$messages" \
        --arg temp "$TEMPERATURE" \
        '{model: $model, messages: $messages, temperature: ($temp | tonumber)}')
    
    # Make the API call
    local response
    response=$(curl -s -X POST "$api_url" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $api_key" \
        -d "$request_body")
    
    # Check for errors
    if echo "$response" | jq -e '.error' >/dev/null 2>&1; then
        log_error "API Error: $(echo "$response" | jq -r '.error.message // .error')"
        return 1
    fi
    
    # Extract content from response
    echo "$response" | jq -r '.choices[0].message.content'
}

# Execute tool based on parsed action
execute_tool() {
    local tool_name="$1"
    local action_input="$2"
    
    log_debug "Executing tool: $tool_name with input: $action_input"
    
    case "$tool_name" in
        "find_all_matching_files")
            local directory=$(echo "$action_input" | jq -r '.directory // empty')
            local pattern=$(echo "$action_input" | jq -r '.pattern // "*"')
            find_all_matching_files "$directory" "$pattern"
            ;;
        "read_file")
            local file_path=$(echo "$action_input" | jq -r '.file_path // empty')
            read_file "$file_path"
            ;;
        *)
            echo "{\"error\": \"Unknown tool: $tool_name\"}"
            ;;
    esac
}

# Parse LLM response and extract components
parse_response() {
    local response="$1"
    
    # Check for Final Answer
    if echo "$response" | grep -q "Final Answer:"; then
        # Extract everything after "Final Answer:" until end of response
        local final_text=$(echo "$response" | awk '/Final Answer:/{p=1} p' | sed '1s/.*Final Answer:[[:space:]]*//')
        # Remove trailing whitespace
        final_text=$(echo "$final_text" | sed 's/[[:space:]]*$//')
        
        if [[ -n "$final_text" ]]; then
            # Return the final answer as output
            echo "FINAL:$final_text"
            log_debug "Found final answer"
            return 0
        fi
    fi
    
    # Extract Action using awk (allow whitespace before Action:)
    local action=$(echo "$response" | awk '/Action:/ {sub(/.*Action:[[:space:]]*/, ""); print; exit}')
    
    # Extract Action Input - get everything between "Action Input:" and the next section marker
    local action_input=$(echo "$response" | awk '
        /Action Input:/ {p=1; sub(/.*Action Input:[[:space:]]*/, ""); if (length($0) > 0) print; next}
        /^(Thought:|Action:|Observation:|Final Answer:)/ {if(p) exit}
        p {print}
    ' | tr -d '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    if [[ -n "$action" ]] && [[ -n "$action_input" ]]; then
        echo "ACTION:$action"
        echo "INPUT:$action_input"
        return 0
    fi
    
    return 1
}

# Main ReAct loop
run_react_agent() {
    local prompt="$1"
    local base_directory="$2"
    
    log_info "Starting ReAct agent with model: $MODEL"
    
    # Initialize conversation with system prompt
    local system_msg=$(jq -n --arg content "$REACT_SYSTEM_PROMPT" '{role: "system", content: $content}')
    MEMORY+=("$system_msg")
    
    # Add user prompt with base directory context
    local full_prompt="Base directory for analysis: $base_directory

$prompt"
    
    local user_msg=$(jq -n --arg content "$full_prompt" '{role: "user", content: $content}')
    MEMORY+=("$user_msg")
    
    # ReAct loop
    local step=0
    while [[ $step -lt $MAX_STEPS ]]; do
        ((step++))
        log_info "Step $step/$MAX_STEPS"
        
        # Prepare messages for API call
        local messages="[$(IFS=,; echo "${MEMORY[*]}")]"
        
        # Get LLM response
        local response
        if ! response=$(call_openai_api "$messages"); then
            log_error "Failed to get response from LLM"
            return 1
        fi
        
        log_debug "LLM Response: $response"
        
        # Add assistant response to memory
        local assistant_msg=$(jq -n --arg content "$response" '{role: "assistant", content: $content}')
        MEMORY+=("$assistant_msg")
        
        # Parse response
        local parsed_output
        parsed_output=$(parse_response "$response")
        local parse_result=$?
        
        # Check if we have final answer
        if [[ "$parsed_output" =~ ^FINAL: ]]; then
            # Extract just the final answer part, removing the FINAL: prefix
            FINAL_ANSWER=$(echo "$parsed_output" | sed 's/^FINAL://' | sed '/^[[:space:]]*$/d')
            log_info "Final answer received"
            break
        fi
        
        # If parse was successful and we have action/input
        if [[ $parse_result -eq 0 ]] && [[ -n "$parsed_output" ]]; then
            
            # Extract action and input
            local action=$(echo "$parsed_output" | grep "^ACTION:" | sed 's/ACTION://')
            local action_input=$(echo "$parsed_output" | grep "^INPUT:" | sed 's/INPUT://')
            
            if [[ -n "$action" ]] && [[ -n "$action_input" ]]; then
                # Execute tool
                local observation
                observation=$(execute_tool "$action" "$action_input")
                
                # Add observation to memory
                local obs_msg=$(jq -n --arg content "Observation: $observation" '{role: "user", content: $content}')
                MEMORY+=("$obs_msg")
                
                log_debug "Tool result: ${#observation} chars"
            fi
        else
            # No valid action found, might be continuation or error
            log_debug "No valid action found in response"
        fi
    done
    
    if [[ -z "$FINAL_ANSWER" ]]; then
        log_error "Failed to complete analysis within $MAX_STEPS steps"
        return 1
    fi
    
    echo "$FINAL_ANSWER"
}

# Save results to file
save_results() {
    local content="$1"
    local repo_name="$2"
    local extension="${3:-.md}"
    local file_name="$4"
    
    mkdir -p "$OUTPUT_DIR"
    
    local timestamp=$(date +"%Y%m%d-%H%M%S")
    local vendor="${MODEL%%/*}"
    local model_id="${MODEL#*/}"
    local safe_model=$(sanitize_filename "$model_id")
    
    local output_file
    if [[ -n "$file_name" ]]; then
        output_file="${OUTPUT_DIR}/${file_name}"
    else
        output_file="${OUTPUT_DIR}/${timestamp}-${repo_name}-${vendor}-${safe_model}${extension}"
    fi
    
    echo "$content" > "$output_file"
    log_info "Results saved to: $output_file"
    echo "$output_file"
}

# Create metadata file
create_metadata() {
    local output_file="$1"
    local repo_url="$2"
    local repo_name="$3"
    
    local metadata_file="${output_file%.md}.metadata.json"
    # macOS date doesn't support %N for nanoseconds
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.000000Z")
    
    jq -n \
        --arg model "$MODEL" \
        --arg url "$repo_url" \
        --arg name "$repo_name" \
        --arg ts "$timestamp" \
        '{model: $model, github_url: $url, repo_name: $name, timestamp: $ts}' \
        > "$metadata_file"
    
    log_info "Metadata saved to: $metadata_file"
}

# Clone or update repository
clone_or_update_repo() {
    local repo_url="$1"
    
    # Extract repo name from URL
    local repo_name=$(basename "$repo_url" .git)
    local owner=$(basename "$(dirname "$repo_url")")
    local cache_path="${CACHE_DIR}/${owner}/${repo_name}"
    
    mkdir -p "$(dirname "$cache_path")"
    
    if [[ -d "$cache_path/.git" ]]; then
        log_info "Updating existing repository: $cache_path"
        (cd "$cache_path" && git pull --quiet)
    else
        log_info "Cloning repository: $repo_url"
        git clone --quiet "$repo_url" "$cache_path"
    fi
    
    echo "$cache_path"
}

# Main function
main() {
    local directory=""
    local prompt_file=""
    local repo_url=""
    local extension=".md"
    local file_name=""
    local eval_prompt=""
    
    # Check dependencies first
    check_dependencies
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --repo)
                repo_url="$2"
                shift 2
                ;;
            --prompt)
                prompt_file="$2"
                shift 2
                ;;
            --cache-dir)
                CACHE_DIR="$2"
                shift 2
                ;;
            --output-dir)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --extension)
                extension="$2"
                shift 2
                ;;
            --file-name)
                file_name="$2"
                shift 2
                ;;
            --eval-prompt)
                eval_prompt="$2"
                shift 2
                ;;
            --model)
                MODEL="$2"
                shift 2
                ;;
            --base-url)
                BASE_URL="$2"
                shift 2
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [directory] [options]

Analyse a codebase using an LLM agent.

Positional arguments:
  directory             Directory containing the codebase to analyse

Options:
  --repo REPO           GitHub repository URL to clone (e.g. https://github.com/owner/repo)
  --prompt FILE         Path to a file containing the analysis prompt (required)
  --cache-dir DIR       Directory to cache cloned repositories (default: ~/.cache/github)
  --output-dir DIR      Directory to save results to (default: output)
  --extension EXT       File extension for output files (default: .md)
  --file-name FILE      Specific file name for output (overrides --extension)
  --eval-prompt FILE    Path to file containing prompt to evaluate the tech writer results
  --model MODEL         Model to use (format: vendor/model, default: openai/gpt-4o-mini)
  --base-url URL        Base URL for the API (automatically set based on model if not provided)
  -h, --help            Show this help message and exit

Dependencies:
  This script requires: jq, curl, git
  Install on macOS: brew install jq
  Install on Ubuntu: sudo apt-get install jq
EOF
                exit 0
                ;;
            *)
                if [[ -z "$directory" ]] && [[ -z "$repo_url" ]]; then
                    directory="$1"
                else
                    echo "Error: Unknown argument: $1" >&2
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Initialize logging
    log_init
    
    # Validate arguments
    if [[ -z "$prompt_file" ]]; then
        log_error "Error: prompt_file is required"
        exit 1
    fi
    
    if [[ ! -f "$prompt_file" ]]; then
        log_error "Error: Prompt file not found: $prompt_file"
        exit 1
    fi
    
    # Read prompt
    local prompt=$(cat "$prompt_file")
    
    # Handle repository or directory
    if [[ -n "$repo_url" ]]; then
        directory=$(clone_or_update_repo "$repo_url")
        repo_name=$(basename "$repo_url" .git)
    else
        if [[ -z "$directory" ]]; then
            directory="."
        fi
        if [[ ! -d "$directory" ]]; then
            log_error "Error: Directory not found: $directory"
            exit 1
        fi
        directory=$(cd "$directory" && pwd)
        repo_name=$(basename "$directory")
    fi
    
    # Run the agent
    local analysis_result
    if analysis_result=$(run_react_agent "$prompt" "$directory"); then
        # Save results
        local output_file
        output_file=$(save_results "$analysis_result" "$repo_name" "$extension" "$file_name")
        
        # Create metadata
        create_metadata "$output_file" "$repo_url" "$repo_name"
        
        # Run evaluation if requested
        if [[ -n "$eval_prompt" ]] && [[ -f "$eval_prompt" ]]; then
            log_info "Running evaluation with prompt: $eval_prompt"
            # TODO: Implement evaluation
        fi
    else
        log_error "Analysis failed"
        exit 1
    fi
}

# Run main function
main "$@"