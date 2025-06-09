#!/bin/bash
# Script to run the original tech writer agent with the existing virtual environment

# Default values
DEFAULT_DIRECTORY="."
DEFAULT_PROMPT="prompt.txt"
DEFAULT_MODEL="gpt-4.1-mini"
DEFAULT_REPO=""
DEFAULT_OUTPUT_DIR=""
DEFAULT_EXTENSION=""
DEFAULT_EVAL_PROMPT=""

# Parse command line arguments
DIRECTORY=$DEFAULT_DIRECTORY
PROMPT_FILE=$DEFAULT_PROMPT
MODEL=$DEFAULT_MODEL
REPO=$DEFAULT_REPO
OUTPUT_DIR=$DEFAULT_OUTPUT_DIR
EXTENSION=$DEFAULT_EXTENSION
EVAL_PROMPT=$DEFAULT_EVAL_PROMPT

# Function to display usage information
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --dir DIR         Directory to analyze (default: current directory)"
    echo "  --prompt FILE     Path to prompt file (default: prompt.txt)"
    echo "  --model MODEL     Model to use (default: gpt-4.1-mini)"
    echo "  --repo REPO       Repository to use (default: none)"
    echo "  --output-dir DIR  Directory to save results to (default: output)"
    echo "  --extension EXT   File extension for output files (default: .md)"
    echo "  --eval-prompt FILE Path to evaluation prompt file (optional)"
    echo "  --help            Show this help message"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)
            DIRECTORY="$2"
            shift 2
            ;;
        --prompt)
            PROMPT_FILE="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --repo)
            REPO="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --extension)
            EXTENSION="$2"
            shift 2
            ;;
        --eval-prompt)
            EVAL_PROMPT="$2"
            shift 2
            ;;
        --output)
            # Ignore output parameter as it's not supported by the original script
            echo "Note: --output parameter is not supported by the original tech writer script."
            echo "Results will be saved to an auto-generated file."
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

# Check if directory exists
if [ ! -d "$DIRECTORY" ]; then
    echo "Error: Directory '$DIRECTORY' does not exist."
    exit 1
fi

# Check if prompt file exists
if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: Prompt file '$PROMPT_FILE' does not exist."
    echo "Using the default prompt.txt file..."
    PROMPT_FILE="prompt.txt"
fi

# Activate the existing virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY not found in environment variables."
    echo "Please set your OpenAI API key before running this script."
    exit 1
fi

# Build command
if [ -n "$REPO" ]; then
    CMD="source .venv/bin/activate && python tech-writer.py --repo \"$REPO\" \"$PROMPT_FILE\" --model \"$MODEL\""
else
    CMD="source .venv/bin/activate && python tech-writer.py \"$DIRECTORY\" \"$PROMPT_FILE\" --model \"$MODEL\""
fi

# Add optional output-dir parameter
if [ -n "$OUTPUT_DIR" ]; then
    CMD="$CMD --output-dir \"$OUTPUT_DIR\""
fi

# Add optional extension parameter
if [ -n "$EXTENSION" ]; then
    CMD="$CMD --extension \"$EXTENSION\""
fi

# Add optional eval-prompt parameter
if [ -n "$EVAL_PROMPT" ]; then
    CMD="$CMD --eval-prompt \"$EVAL_PROMPT\""
fi

# Run the tech writer agent
echo "Running original tech writer agent..."
echo "Command: $CMD"
eval $CMD

# Deactivate virtual environment
deactivate

echo "Analysis complete."
