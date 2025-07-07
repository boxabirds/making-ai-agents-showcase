# Tech Writer Agent - PHP Implementation

A PHP implementation of the tech writer agent. This agent analyzes codebases and generates comprehensive documentation using a ReAct pattern.

## Features

- Pure PHP implementation
- ReAct (Reasoning and Acting) agent pattern
- Support for OpenAI and Google Gemini models
- GitHub repository cloning and caching
- Structured markdown output with metadata
- Respects .gitignore files when exploring codebases

## Prerequisites

- PHP 7.4 or higher
- Composer (PHP package manager)
- OpenAI API key or Google Gemini API key

## Installation

Install dependencies using Composer:

```bash
composer install
```

Or let the wrapper script handle it automatically:

```bash
./tech-writer.sh --help
```

## Usage

```bash
./tech-writer.sh [directory] --prompt prompt.txt [options]
```

Or directly with PHP:

```bash
php tech-writer.php [directory] --prompt prompt.txt [options]
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

## Dependencies

This implementation uses:
- `guzzlehttp/guzzle` - HTTP client for API calls
- `openai-php/client` - OpenAI PHP client
- `symfony/finder` - File system traversal
- `monolog/monolog` - Logging

See `composer.json` for the full list of dependencies.