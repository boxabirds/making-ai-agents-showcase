#!/bin/bash

# Tech Writer Agent Launcher Script for Rust implementation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build if binary doesn't exist or is outdated
if [ ! -f "$SCRIPT_DIR/target/release/tech-writer-agent" ] || [ "$SCRIPT_DIR/src/main.rs" -nt "$SCRIPT_DIR/target/release/tech-writer-agent" ]; then
    echo "Building tech-writer-agent..." >&2
    (cd "$SCRIPT_DIR" && cargo build --release)
fi

# Execute the Rust tech writer
exec "$SCRIPT_DIR/target/release/tech-writer-agent" "$@"