# Tech Writer Agent - Go Implementation

This is a Go port of the Python tech-writer agent, designed to expose all the mechanisms required for interacting with language models, tool calling, and building agents from scratch.

## Project Structure

```
tech-writer-agent/
├── main.go           # Entry point and command-line interface
├── agent.go          # ReAct agent implementation
├── tools.go          # Tool implementations (find_files, read_file)
├── llm.go            # Language model client (OpenAI/Gemini)
├── utils.go          # Utility functions
└── go.mod            # Go module definition
```

## Features (To Be Implemented)

1. **Command-line Interface** - Matching the Python version's arguments
2. **ReAct Agent Pattern** - Manual implementation of the reasoning and acting loop
3. **Tool System** - Native Go implementations of file system tools
4. **Multi-Model Support** - OpenAI and Google Gemini support
5. **Repository Cloning** - GitHub repository analysis capability
6. **Metadata Generation** - Output metadata in JSON format

## Usage

```bash
# Analyze current directory
./tech-writer-agent . --prompt prompt.txt --model openai/gpt-4o-mini

# Analyze specific directory  
./tech-writer-agent /path/to/code --prompt prompt.txt --model google/gemini-2.0-flash

# Clone and analyze a GitHub repository
./tech-writer-agent --repo https://github.com/owner/repo --prompt prompt.txt --model openai/gpt-4o

# Specify output directory and format
./tech-writer-agent . --prompt prompt.txt --output-dir results --extension .md
```

## Command Line Arguments

- First positional: Directory path to analyze
- `--prompt` - Path to prompt file (required)
- `--repo` - GitHub repository URL to analyze instead of local directory
- `--model` - Model name in vendor/model format (default: openai/gpt-4o-mini)
- `--output-dir` - Output directory (default: output)
- `--cache-dir` - Cache directory for repos (default: ~/.cache/github)
- `--extension` - File extension for output (default: .md)
- `--file-name` - Specific output filename (overrides extension)
- `--eval-prompt` - Path to evaluation prompt file (optional)
- `--base-url` - Custom API endpoint

## Environment Variables

- `OPENAI_API_KEY` - Required for OpenAI models
- `GEMINI_API_KEY` - Required for Google models

## Building

```bash
go build -o tech-writer-agent
```

## Implementation Status

- [x] Command-line argument parsing
- [x] Basic project structure
- [ ] Language model client (OpenAI/Gemini)
- [ ] Tool implementations
- [ ] ReAct agent logic
- [ ] Repository cloning
- [ ] Result saving and metadata
- [ ] Error handling and logging

## Design Principles

This is a "baremetal" implementation, meaning:
- No agent frameworks or abstractions
- Direct API calls to language models
- Manual implementation of tool calling
- Explicit handling of the ReAct loop
- Educational focus on understanding the underlying mechanisms

## Next Steps

1. Implement the language model client with support for OpenAI and Gemini
2. Port the tool functions from Python to Go
3. Implement the ReAct agent logic
4. Add repository cloning functionality
5. Complete result saving and metadata generation