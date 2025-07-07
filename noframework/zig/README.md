# Tech Writer Agent - Zig Implementation

A Zig implementation of the tech writer agent. This agent analyzes codebases and generates comprehensive documentation using a ReAct pattern.

## Features

- Pure Zig implementation
- ReAct (Reasoning and Acting) agent pattern
- Support for OpenAI and Google Gemini models
- GitHub repository cloning and caching
- Structured markdown output with metadata
- Respects .gitignore files when exploring codebases

## Prerequisites

- Zig 0.12.0 or higher
- Git
- OpenAI API key or Google Gemini API key

## Building

The wrapper script automatically builds the executable:

```bash
./tech-writer.sh --help
```

Or build manually:

```bash
zig build -Doptimize=ReleaseFast
```

## Usage

```bash
./tech-writer.sh [directory] --prompt prompt.txt [options]
```

### Options

- `--repo REPO` - GitHub repository URL to clone (e.g. https://github.com/owner/repo)
- `--prompt FILE` - Path to a file containing the analysis prompt (required)
- `--cache-dir DIR` - Directory to cache cloned repositories (default: ~/.cache/github)
- `--output-dir DIR` - Directory to save results to (default: output)
- `--extension EXT` - File extension for output files (default: .md)
- `--file-name FILE` - Specific file name for output (overrides --extension)
- `--model MODEL` - Model to use (format: vendor/model, default: openai/gpt-4o-mini)
- `--base-url URL` - Base URL for the API (automatically set based on model if not provided)

### Examples

Analyze a local directory:
```bash
./tech-writer.sh /path/to/project --prompt analysis-prompt.txt
```

Analyze a GitHub repository:
```bash
./tech-writer.sh --repo https://github.com/axios/axios --prompt analysis-prompt.txt
```

Use a different model:
```bash
./tech-writer.sh --repo https://github.com/axios/axios --prompt analysis-prompt.txt --model google/gemini-2.0-flash
```

## Environment Variables

Set one of these API keys:
- `OPENAI_API_KEY` - For OpenAI models
- `GEMINI_API_KEY` - For Google Gemini models

## Output

The agent generates:
- A markdown file with the analysis results
- A metadata JSON file with model info and timestamps

Results are saved in the `output` directory by default.

## Implementation Details

This implementation uses Zig's standard library for:
- HTTP client for API calls
- JSON parsing and generation
- File system operations
- Process execution (for git operations)

The agent follows the same ReAct pattern as other implementations, providing consistent behavior across all languages.