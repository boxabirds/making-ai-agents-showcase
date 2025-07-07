#!/bin/bash

# Tech Writer Agent Launcher Script for Go implementation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$SCRIPT_DIR/tech-writer-agent"

# Build if binary doesn't exist
if [ ! -f "$AGENT_DIR/tech-writer-agent" ]; then
    echo "Building tech-writer-agent..." >&2
    (cd "$AGENT_DIR" && go build -o tech-writer-agent)
fi

# Convert double-dash arguments to single-dash for Go's flag package
args=()
i=1
while [[ $i -le $# ]]; do
    arg="${!i}"
    
    if [[ "$arg" == --* ]]; then
        # Convert --foo to -foo
        args+=("-${arg:2}")
    else
        # Keep everything else as is
        args+=("$arg")
    fi
    
    ((i++))
done

# Execute the Go tech writer with converted arguments
exec "$AGENT_DIR/tech-writer-agent" "${args[@]}"