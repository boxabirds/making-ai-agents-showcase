#!/bin/bash

# Tech Writer Agent Launcher Script for PHP implementation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if vendor directory exists, if not run composer install
if [ ! -d "$SCRIPT_DIR/vendor" ]; then
    echo "Installing dependencies..." >&2
    (cd "$SCRIPT_DIR" && composer install --no-interaction)
fi

# Execute the PHP tech writer
exec php "$SCRIPT_DIR/tech-writer.php" "$@"