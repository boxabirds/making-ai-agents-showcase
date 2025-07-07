#!/bin/bash

# Tech Writer Agent Launcher Script for TypeScript implementation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Execute the TypeScript tech writer with bun
exec bun run "$SCRIPT_DIR/tech-writer.ts" "$@"