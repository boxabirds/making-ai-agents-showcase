# DSPy Tech Writer Agent

This directory contains two DSPy implementations of the tech writer agent, providing the same functionality as the baremetal implementation but using Stanford's DSPy framework.

## Files

- `tech-writer.py` - Full tech writer agent implementation using manual DSPy signatures
- `tech-writer.sh` - Shell script wrapper for running the manual signatures version
- `tech-writer-react.py` - Simplified implementation using DSPy's built-in ReAct module
- `tech-writer-react.sh` - Shell script wrapper for running the ReAct version
- `demo-customer-service.py` - Example DSPy agent demonstrating basic functionality
- `test-prompt.txt` - Simple test prompt for verification

## Running the Tech Writer

Both implementations accept the same command-line arguments as the baremetal version:

```bash
# Using manual signatures approach
./tech-writer.sh --repo https://github.com/owner/repo --prompt prompts/api-guide.prompt.txt --model openai/gpt-4o

# Using built-in ReAct module (simpler, recommended)
./tech-writer-react.sh --repo https://github.com/owner/repo --prompt prompts/api-guide.prompt.txt --model openai/gpt-4o

# Analyze a local directory
./tech-writer-react.sh /path/to/project --prompt prompts/architecture-overview.prompt.txt --model google/gemini-2.0-flash

# Using Python directly with virtual environment
source .venv/bin/activate && python tech-writer-react.py /my-project --prompt prompt.txt --model openai/gpt-4o-mini
```

### Command Line Arguments

- First positional: Directory path to analyze (or use `--repo`)
- `--prompt` - Path to prompt file (required)
- `--repo` - GitHub repository URL to analyze instead of local directory
- `--model` - Model name in vendor/model format (default: openai/gpt-4o-mini)
- `--output-dir` - Output directory (default: ./output)
- `--cache-dir` - Cache directory for repos (default: ~/.cache/github)
- `--extension` - File extension for output (default: .md)
- `--file-name` - Specific output filename (overrides extension)
- `--eval-prompt` - Path to evaluation prompt file (optional)

## Key Features

1. **DSPy Signatures**: Uses declarative signatures for tool calling and final answer generation
2. **ReAct-Style Agent**: Implements reasoning and acting pattern using DSPy's ChainOfThought
3. **Tool Integration**: Wraps common tools for DSPy compatibility
4. **Multi-Model Support**: Works with any model supported by DSPy/LiteLLM
5. **Same Interface**: Drop-in replacement for baremetal tech writer

## Implementation Highlights

- **Declarative Approach**: Uses DSPy signatures instead of manual prompt engineering
- **Automatic Optimization**: Can be compiled with DSPy optimizers for better performance
- **Tool Descriptions**: Provides structured tool descriptions for the LLM
- **Error Handling**: Robust error handling for tool execution failures
- **Streaming Support**: Compatible with DSPy's built-in capabilities

## DSPy-Specific Features

### Signatures

The implementation uses three main signatures:

1. **TechWriterSignature**: Main analysis task
2. **ToolCallSignature**: Decides which tool to call and arguments
3. **FinalAnswerSignature**: Generates final documentation

### Tool Integration

Tools from the common directory are wrapped with descriptions:

```python
tool_descriptions = {
    "find_all_matching_files": {
        "name": "find_all_matching_files",
        "description": "Find files matching a pattern while respecting .gitignore",
        "parameters": {...}
    },
    "read_file": {
        "name": "read_file", 
        "description": "Read the contents of a file",
        "parameters": {...}
    }
}
```

### ReAct Loop

The agent implements a ReAct-style loop:

1. Analyze task and decide on tool to use
2. Execute tool and collect observations
3. Repeat until task is complete or max steps reached
4. Generate final documentation from all observations

## Two Implementation Approaches

### 1. Manual Signatures (`tech-writer.py`)
- Uses custom DSPy signatures for each step
- Implements ReAct loop manually
- More control over the process
- Good for learning DSPy concepts
- ~234 lines of code

### 2. Built-in ReAct (`tech-writer-react.py`)
- Uses DSPy's built-in `dspy.ReAct` module
- Automatic tool handling and reasoning
- Much simpler implementation
- Recommended for production use
- ~150 lines of code

## Comparison with Other Implementations

| Aspect | Baremetal | ADK | Agno | DSPy Manual | DSPy ReAct |
|--------|-----------|-----|------|-------------|------------|
| **Framework** | OpenAI Client | Google ADK | phidata | Stanford DSPy | Stanford DSPy |
| **Lines of Code** | 308 | 126 | 111 | 234 | ~150 |
| **Tool Handling** | Manual | Framework | Automatic | Signature-based | Built-in |
| **Execution Model** | Sync | Async | Sync | Sync | Sync |
| **Optimization** | None | None | None | Compilable | Compilable |

## Example Usage

```python
from tech_writer import DSPyTechWriter

# Create agent
agent = DSPyTechWriter(model_name="openai/gpt-4o-mini")

# Run analysis
result = agent(
    prompt="Find all Python files and document their main functions",
    base_directory="/path/to/code"
)

print(result)
```

## Dependencies

- `dspy>=2.6.27` - Core DSPy framework
- `openai>=1.86.0` - OpenAI API client (used by LiteLLM)
- `pydantic>=2.11.5` - Data validation
- `pathspec>=0.12.1` - Gitignore pattern matching
- `gitpython>=3.1.44` - Git repository handling
- `binaryornot>=0.4.4` - Binary file detection
- `chardet>=5.2.0` - Character encoding detection

## Notes

- DSPy uses LiteLLM internally for model connections
- The implementation can be optimized using DSPy's compilation features
- Tool execution is synchronous to match the baremetal interface
- Error messages include full context for debugging