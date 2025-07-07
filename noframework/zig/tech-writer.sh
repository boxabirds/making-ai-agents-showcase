#!/bin/bash

# Tech Writer Agent Launcher Script for Zig implementation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build the Zig executable
(cd "$SCRIPT_DIR" && zig build -Doptimize=ReleaseFast) || exit 1

# Execute the tech writer
exec "$SCRIPT_DIR/zig-out/bin/tech-writer" "$@"