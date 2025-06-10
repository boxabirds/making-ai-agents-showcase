#!/bin/bash
# Run the Agno tech writer agent

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the Python script with all arguments passed through
exec python "$SCRIPT_DIR/tech-writer.py" "$@"