#!/bin/bash

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed."
    echo ""
    echo "To install uv, visit: https://docs.astral.sh/uv/getting-started/installation/"
    echo ""
    
    # Detect platform and offer platform-specific installation
    case "$(uname -s)" in
        Darwin*)
            echo "For macOS, you can install uv using:"
            echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
            echo ""
            read -p "Would you like to install uv now? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                curl -LsSf https://astral.sh/uv/install.sh | sh
                echo "Please restart your terminal or run: source $HOME/.cargo/env"
                exit 0
            fi
            ;;
        Linux*)
            echo "For Linux, you can install uv using:"
            echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
            echo ""
            read -p "Would you like to install uv now? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                curl -LsSf https://astral.sh/uv/install.sh | sh
                echo "Please restart your terminal or run: source $HOME/.cargo/env"
                exit 0
            fi
            ;;
        MINGW*|CYGWIN*|MSYS*)
            echo "For Windows, you can install uv using:"
            echo "  powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
            echo ""
            echo "Please install uv and try again."
            ;;
        *)
            echo "Platform not recognized. Please visit the installation guide."
            ;;
    esac
    exit 1
fi

# Run the script using uv (which automatically uses the virtual environment)
uv run python ./tech-writer.py "$@"
