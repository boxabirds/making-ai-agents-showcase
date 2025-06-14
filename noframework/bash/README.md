# Bash Tech Writer Agent

This directory contains a pure Bash implementation of the tech writer agent, providing the same functionality as the Python version but written entirely in Bash (with CLI tools like `jq`).

## Features

- **Pure Bash Implementation**: No Python dependencies in the main script
- **ReAct Agent Pattern**: Implements the same reasoning and acting loop as the Python version
- **Tool Support**: Includes `find_all_matching_files` and `read_file` tools
- **Multi-Model Support**: Works with OpenAI and Google Gemini models
- **Same Interface**: Compatible command-line arguments and output format

## Requirements

- **bash** 4.0 or higher
- **jq** - Command-line JSON processor
- **curl** - HTTP client
- **git** - For repository cloning
- **file** - For binary file detection

Install dependencies:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq curl git file
```

## Usage

```bash
# Analyze current directory
./tech-writer.sh . prompt.txt --model openai/gpt-4o-mini

# Analyze specific directory
./tech-writer.sh /path/to/code prompt.txt --model google/gemini-2.0-flash

# Clone and analyze a GitHub repository
./tech-writer.sh --repo https://github.com/owner/repo prompt.txt --model openai/gpt-4o

# Specify output directory and format
./tech-writer.sh . prompt.txt --output-dir results --extension .md
```

### Command Line Arguments

- First positional: Directory path to analyze
- Second positional: Path to prompt file (required)
- `--repo REPO` - GitHub repository URL to clone and analyze
- `--model MODEL` - Model in vendor/model format (default: openai/gpt-4o-mini)
- `--output-dir DIR` - Output directory (default: output)
- `--cache-dir DIR` - Cache directory for repos (default: ~/.cache/github)
- `--extension EXT` - File extension for output (default: .md)
- `--file-name FILE` - Specific output filename
- `--eval-prompt FILE` - Evaluation prompt file (optional)
- `--base-url URL` - Custom API endpoint

## Environment Variables

- `OPENAI_API_KEY` - Required for OpenAI models
- `GEMINI_API_KEY` - Required for Google models

## Implementation Details

### Tools

1. **find_all_matching_files**
   - Finds files matching glob patterns
   - Respects .gitignore by default
   - Handles hidden files and subdirectories

2. **read_file**
   - Reads file contents
   - Detects and skips binary files
   - Returns JSON-formatted response

### JSON Handling

- Uses `jq` for reliable JSON parsing and creation
- Properly escapes special characters in file contents
- Handles nested JSON structures in tool inputs/outputs

### ReAct Loop

1. Sends system prompt with ReAct instructions
2. Parses LLM responses for actions and inputs
3. Executes tools and adds observations to memory
4. Continues until "Final Answer" is found
5. Saves results and metadata

### Logging

- Creates timestamped log files in `logs/` directory
- Logs all tool invocations and results
- Debug mode shows full LLM responses
- Stderr is used for logs to keep stdout clean

## Differences from Python Version

1. **JSON Escaping**: Uses `jq` instead of Python's json module
2. **Date Handling**: Simplified timestamps for macOS compatibility
3. **Memory Management**: Uses bash arrays instead of Python lists
4. **Error Handling**: Relies on bash's `set -euo pipefail`
5. **Tool Results**: Direct JSON string manipulation

## Example

```bash
# Create a prompt file
echo "Find all shell scripts and describe their purpose." > prompt.txt

# Run the analysis
./tech-writer.sh . prompt.txt --model openai/gpt-4o-mini

# Check the output
cat output/20250611-*.md
```

## Troubleshooting

1. **Missing jq**: Install with package manager
2. **API Errors**: Check API keys are set correctly
3. **Empty Results**: Check logs in `logs/` directory
4. **Parsing Errors**: Ensure prompt follows ReAct format

## Notes

- The script requires bash 4.0+ for associative arrays and other features
- All file paths are properly quoted to handle spaces
- Git ignore patterns are respected when searching files
- Binary files are automatically detected and skipped
- The implementation is functionally identical to the Python version