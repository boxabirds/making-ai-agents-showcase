#!/bin/bash
# Script to generate installation instructions using the tech writer agent

# Set the base directory to the parent directory (awesome-agent-showcase)
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Default values
DEFAULT_MODEL="gpt-4.1-mini"
DEFAULT_REPO=""
DEFAULT_TEST_REPO_FILE="test-repos.txt"

# Parse command line arguments
MODEL=$DEFAULT_MODEL
REPO=$DEFAULT_REPO
TEST_MODE=false
TEST_REPO_FILE=$DEFAULT_TEST_REPO_FILE

# Function to display usage information
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --model MODEL         Model to use (default: gpt-4.1-mini)"
    echo "  --repo REPO           Repository to analyze instead of local directory"
    echo "  --test                Run test mode on multiple repositories"
    echo "  --test-repo-file FILE File containing list of repos (default: test-repos.txt)"
    echo "  --help                Show this help message"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --repo)
            REPO="$2"
            shift 2
            ;;
        --test)
            TEST_MODE=true
            shift
            ;;
        --test-repo-file)
            TEST_REPO_FILE="$2"
            shift 2
            ;;
        --help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Change to the baseline directory where tech-writer.py is located
cd "$BASE_DIR/baseline"

# Function to run tech writer on a single repo
function analyze_repo {
    local repo="$1"
    echo "Analyzing repository: $repo"
    ./tech-writer.sh --prompt ../setup/install-instructions.prompt.txt --repo "$repo" --model "$MODEL" --output-dir "../setup/output" --extension "sh"
}

# Test mode: process multiple repositories from file
if [ "$TEST_MODE" = true ]; then
    # Check if test repo file exists
    if [ ! -f "../setup/$TEST_REPO_FILE" ]; then
        echo "Error: Test repository file not found: $TEST_REPO_FILE"
        exit 1
    fi
    
    echo "Running in test mode with repositories from: $TEST_REPO_FILE"
    echo "================================================="
    
    # Read repos from file and process each one
    while IFS= read -r repo || [ -n "$repo" ]; do
        # Skip empty lines and lines starting with #
        if [[ -z "$repo" || "$repo" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Trim whitespace
        repo=$(echo "$repo" | xargs)
        
        analyze_repo "$repo"
        echo "================================================="
    done < "../setup/$TEST_REPO_FILE"
    
    echo "Test mode complete. All repositories processed."
    
# Single repo or directory mode
else
    # Build the command
    if [ -n "$REPO" ]; then
        # If repo is specified, use it
        analyze_repo "$REPO"
    else
        # Otherwise analyze the local directory
        ./tech-writer.sh --prompt ../setup/install-instructions.prompt.txt --dir "$BASE_DIR" --model "$MODEL" --output-dir "../setup/output" --extension "sh"
    fi
fi