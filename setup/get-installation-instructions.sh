#!/bin/bash
# Script to run the original tech writer agent with the existing virtual environment

# Default values
DEFAULT_DIRECTORY="."
DEFAULT_PROMPT="prompt.txt"
DEFAULT_MODEL="google/gemini-3-4b"
DEFAULT_AGENT_TYPE="react"
DEFAULT_REPO=""

# Parse command line arguments
DIRECTORY=$DEFAULT_DIRECTORY
PROMPT_FILE=$DEFAULT_PROMPT
MODEL=$DEFAULT_MODEL
AGENT_TYPE=$DEFAULT_AGENT_TYPE
REPO=$DEFAULT_REPO

# Function to display usage information
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --dir DIR       Directory to analyze (default: current directory)"
    echo "  --prompt FILE   Path to prompt file (default: prompt.txt)"
    echo "  --model MODEL   Model to use (default: gpt-4o-mini)"
    echo "  --agent-type TYPE    Agent type to use (default: ReAct)"
    echo "                  Available types: ReAct, Reflexion"
    echo "  --repo REPO     Repository to use (default: none)"
    echo "  --help          Show this help message"
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
        --agent-type)
            AGENT_TYPE="$2"
            shift 2
            ;;
        --repo)
            REPO="$2"
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
    CMD="source .venv/bin/activate && python tech-writer-from-scratch.py --repo \"$REPO\" \"$PROMPT_FILE\" --model \"$MODEL\" --agent-type \"$AGENT_TYPE\""
else
    CMD="source .venv/bin/activate && python tech-writer-from-scratch.py \"$DIRECTORY\" \"$PROMPT_FILE\" --model \"$MODEL\" --agent-type \"$AGENT_TYPE\""
fi

# Run the tech writer agent
echo "Running original tech writer agent..."
echo "Command: $CMD"
eval $CMD

# Deactivate virtual environment
deactivate

echo "Analysis complete."
