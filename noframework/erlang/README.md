# Tech Writer Agent - Erlang Implementation

A pure Erlang implementation of the tech writer agent that analyzes codebases and generates technical documentation using a ReAct-style approach.

## Prerequisites

- Erlang/OTP 24 or higher
- rebar3 (will be installed automatically if not present)

## Installation

The `tech-writer.sh` script will automatically install Erlang and rebar3 if they're not already installed.

## Usage

```bash
./tech-writer.sh --repo https://github.com/owner/repo --prompt prompt.txt
```

### Options

- `--repo URL`: GitHub repository URL to analyze (required)
- `--prompt FILE`: Path to file containing the analysis prompt (required)
- `--output-dir DIR`: Directory to save results (default: `output`)
- `--file-name NAME`: Output file name (default: timestamped)
- `--model MODEL`: LLM model to use (default: `openai/gpt-4o-mini`)

### Examples

Basic usage:
```bash
./tech-writer.sh \
  --repo https://github.com/axios/axios \
  --prompt ../prompts/analyze.txt
```

With custom output:
```bash
./tech-writer.sh \
  --repo https://github.com/facebook/react \
  --prompt ../prompts/architecture.txt \
  --output-dir results \
  --file-name react-analysis.md
```

## Features

- Pure Erlang implementation using OTP principles
- Automatic dependency management with rebar3
- HTTP client using hackney
- JSON handling with jsx
- Git repository caching
- Structured logging
- ReAct-style agent loop
- Temperature set to 0 for deterministic outputs

## Implementation Details

- Uses Erlang's pattern matching for argument parsing
- Leverages OTP's supervision trees for reliability
- Implements the ReAct pattern with recursive loops
- File operations use Erlang's built-in file module
- HTTP requests handled by hackney for better performance

## Environment Variables

- `OPENAI_API_KEY`: Required for OpenAI models
- `GEMINI_API_KEY`: Required for Google Gemini models