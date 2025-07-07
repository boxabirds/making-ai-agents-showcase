#!/bin/bash

# Tech Writer Agent Launcher Script for Erlang implementation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Erlang is installed
if ! command -v erl >/dev/null 2>&1; then
    echo "Erlang is not installed. Installing..." >&2
    
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        if command -v brew >/dev/null 2>&1; then
            brew install erlang
        else
            echo "Please install Homebrew first: https://brew.sh" >&2
            exit 1
        fi
    elif [[ -f /etc/debian_version ]]; then
        # Debian/Ubuntu
        sudo apt-get update && sudo apt-get install -y erlang
    elif [[ -f /etc/redhat-release ]]; then
        # RHEL/CentOS/Fedora
        sudo yum install -y erlang
    else
        echo "Please install Erlang manually for your system" >&2
        exit 1
    fi
fi

# Add local bin to PATH for rebar3
export PATH="$HOME/.local/bin:$PATH"

# Check if rebar3 is installed (Erlang build tool)
if ! command -v rebar3 >/dev/null 2>&1; then
    echo "Installing rebar3..." >&2
    # Install to user's local bin directory instead of system-wide
    mkdir -p "$HOME/.local/bin"
    if ! [ -f "$HOME/.local/bin/rebar3" ]; then
        wget https://s3.amazonaws.com/rebar3/rebar3 -O "$HOME/.local/bin/rebar3"
        chmod +x "$HOME/.local/bin/rebar3"
    fi
fi

# Check if dependencies need to be fetched
if [ ! -d "$SCRIPT_DIR/_build" ]; then
    echo "Fetching dependencies..." >&2
    (cd "$SCRIPT_DIR" && rebar3 compile)
fi

# Convert arguments to Erlang format
# Erlang expects arguments as a list of atoms/strings
ARGS=""
for arg in "$@"; do
    # Escape backslashes and quotes properly for Erlang
    escaped_arg=$(echo "$arg" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')
    if [ -z "$ARGS" ]; then
        ARGS="\"$escaped_arg\""
    else
        ARGS="$ARGS, \"$escaped_arg\""
    fi
done

# Add the compiled app to the path
ERL_LIBS="$SCRIPT_DIR/_build/default/lib"

# Run the Erlang tech writer
# Load all dependency paths
ERL_PATHS=""
for dir in "$SCRIPT_DIR"/_build/default/lib/*/ebin; do
    ERL_PATHS="$ERL_PATHS -pa $dir"
done

exec erl $ERL_PATHS \
         -noshell \
         -eval "tech_writer:main([$ARGS])." \
         -s init stop