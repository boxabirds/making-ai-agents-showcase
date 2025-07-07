#!/bin/bash

# Script to update all tech-writer.sh files with uv detection and simplified command

# Function to create the new tech-writer.sh content
create_new_content() {
cat << 'EOF'
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
EOF
}

# Find all tech-writer.sh files
echo "Finding all tech-writer.sh files..."
tech_writer_files=$(find .. -name "tech-writer.sh" -type f)

# Update each file
for file in $tech_writer_files; do
    echo "Updating: $file"
    
    # Create new content
    new_content=$(create_new_content)
    
    # Write the new content
    echo "$new_content" > "$file"
    
    # Make it executable
    chmod +x "$file"
done

echo "Updated $(echo "$tech_writer_files" | wc -l | tr -d ' ') tech-writer.sh files"