# Tech Writer Agent - TypeScript Implementation with Bun

A TypeScript implementation of the tech writer agent using Bun runtime. This agent analyzes codebases and generates comprehensive documentation using a ReAct pattern.

## Features

- Pure TypeScript implementation using Bun
- ReAct (Reasoning and Acting) agent pattern
- Support for OpenAI and Google Gemini models
- GitHub repository cloning and caching
- Structured markdown output with metadata

## Prerequisites

- [Bun](https://bun.sh/) runtime installed
- OpenAI API key or Google Gemini API key

## Installation

```bash
bun install
```

## Usage

```bash
./tech-writer.sh [directory] --prompt prompt.txt [options]
```

Or directly with Bun:

```bash
bun run tech-writer.ts [directory] --prompt prompt.txt [options]
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
- `-h, --help` - Show help message

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
