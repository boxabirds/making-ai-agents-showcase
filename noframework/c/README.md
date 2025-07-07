# Tech Writer Agent - C Implementation

A portable C implementation of the tech writer agent. This agent analyzes codebases and generates comprehensive documentation using a ReAct pattern.

## Features

- Pure C implementation with minimal dependencies
- Cross-platform support (Linux, macOS, Windows)
- ReAct (Reasoning and Acting) agent pattern
- Support for OpenAI and Google Gemini models
- GitHub repository cloning and caching
- Structured markdown output with metadata
- Respects .gitignore files when exploring codebases

## Prerequisites

- C compiler (gcc, clang, or MSVC)
- libcurl development libraries
- Git
- OpenAI API key or Google Gemini API key

### Installing Dependencies

**macOS (Homebrew):**
```bash
brew install curl
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install build-essential libcurl4-openssl-dev
```

**RHEL/CentOS/Fedora:**
```bash
sudo dnf install gcc make libcurl-devel
```

**Windows:**
- Install Visual Studio with C++ development tools
- Or use MinGW/MSYS2 with libcurl

## Building

```bash
make
```

Or use the wrapper script which builds automatically:

```bash
./tech-writer.sh --help
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

This implementation uses:
- libcurl for HTTP requests
- cJSON for JSON parsing (included)
- Platform abstraction layer for Windows/POSIX compatibility
- POSIX-compliant directory traversal with Windows fallbacks

The code is written in portable C99 with platform-specific code isolated in `platform.c`.