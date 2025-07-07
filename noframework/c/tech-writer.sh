#!/bin/bash

# Tech Writer Agent Launcher Script for C implementation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build the C executable if it doesn't exist or if source files are newer
if [ ! -f "$SCRIPT_DIR/tech-writer" ] || [ "$SCRIPT_DIR/src/main.c" -nt "$SCRIPT_DIR/tech-writer" ]; then
    echo "Building tech-writer..." >&2
    (cd "$SCRIPT_DIR" && make clean && make) || exit 1
fi

# Execute the tech writer
exec "$SCRIPT_DIR/tech-writer" "$@"