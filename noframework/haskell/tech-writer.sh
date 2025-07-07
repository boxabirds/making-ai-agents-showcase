#!/bin/bash

# Tech Writer Agent Launcher Script for Haskell implementation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if GHC is installed
if ! command -v ghc >/dev/null 2>&1; then
    echo "GHC (Glasgow Haskell Compiler) is not installed. Installing..." >&2
    
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        if command -v brew >/dev/null 2>&1; then
            brew install ghc cabal-install
        else
            echo "Please install Homebrew first: https://brew.sh" >&2
            exit 1
        fi
    elif [[ -f /etc/debian_version ]]; then
        # Debian/Ubuntu
        sudo apt-get update && sudo apt-get install -y ghc cabal-install
    elif [[ -f /etc/redhat-release ]]; then
        # RHEL/CentOS/Fedora
        sudo yum install -y ghc cabal-install
    else
        echo "Please install GHC and Cabal manually for your system" >&2
        exit 1
    fi
fi

# Check if cabal is installed
if ! command -v cabal >/dev/null 2>&1; then
    echo "Cabal is not installed. Please install it along with GHC." >&2
    exit 1
fi

# Build if binary doesn't exist
if [ ! -f "$SCRIPT_DIR/tech-writer" ]; then
    echo "Building tech-writer..." >&2
    (cd "$SCRIPT_DIR" && cabal update && cabal build && cp $(cabal list-bins) tech-writer)
fi

# Execute the Haskell tech writer
exec "$SCRIPT_DIR/tech-writer" "$@"