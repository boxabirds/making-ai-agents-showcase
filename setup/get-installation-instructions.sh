#!/bin/bash
# Script to generate installation instructions using the tech writer agent

# Set the base directory to the parent directory (awesome-agent-showcase)
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Default values
DEFAULT_MODEL="gpt-4.1-mini"
DEFAULT_REPO=""

# Parse command line arguments
MODEL=$DEFAULT_MODEL
REPO=$DEFAULT_REPO
EXTRA_ARGS=""

# Function to display usage information
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --model MODEL   Model to use (default: gpt-4.1-mini)"
    echo "  --repo REPO     Repository to analyze instead of local directory"
    echo "  --help          Show this help message"
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

# Build the command
if [ -n "$REPO" ]; then
    # If repo is specified, use it
    ./tech-writer.sh --prompt ../setup/install-instructions.prompt.txt --repo "$REPO" --model "$MODEL"
else
    # Otherwise analyze the local directory
    ./tech-writer.sh --prompt ../setup/install-instructions.prompt.txt --dir "$BASE_DIR" --model "$MODEL"
fi