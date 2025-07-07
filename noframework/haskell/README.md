# Tech Writer Agent - Haskell Implementation

A pure Haskell implementation of the tech writer agent that analyzes codebases and generates technical documentation using a ReAct-style approach.

## Prerequisites

- GHC (Glasgow Haskell Compiler) 8.10 or higher
- Cabal 3.0 or higher

## Installation

The `tech-writer.sh` script will automatically install GHC and Cabal if they're not already installed.

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

- Pure Haskell implementation with strong type safety
- Automatic dependency management with Cabal
- HTTP client using http-conduit
- JSON handling with aeson
- Git repository caching
- Structured logging
- ReAct-style agent loop
- Temperature set to 0 for deterministic outputs

## Implementation Details

- Uses Haskell's type system for safe argument parsing
- Leverages lazy evaluation for efficient file processing
- Pattern matching for robust error handling
- Functional approach to the ReAct loop
- Regex-based response parsing with regex-tdfa

## Environment Variables

- `OPENAI_API_KEY`: Required for OpenAI models
- `GEMINI_API_KEY`: Required for Google Gemini models