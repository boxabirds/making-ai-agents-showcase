# Tool Integration Patterns Across Agent Frameworks

## Executive Summary

When building AI agents that use tools, a fundamental challenge is passing context (like a working directory) to those tools. After examining the source code of five popular agent frameworks, we discovered three distinct philosophies:

1. **Trust the LLM** (Agno, ADK, DSPy)
   - Pass tools directly with their original signatures
   - Include context in the prompt (e.g., "Base directory: /path")
   - Rely on the LLM to extract context and pass it as parameters
   - Simplest code but depends on LLM capabilities

2. **Trust the Framework** (Pydantic AI)
   - Use dependency injection to automatically provide context
   - Tools receive a `RunContext` with guaranteed access to dependencies
   - Type-safe and reliable but requires more setup
   - The LLM never handles context parameters

3. **Trust the Developer** (LangGraph)
   - Use wrapper functions to manually bind context
   - Create closures that capture the directory from scope
   - Most explicit and verbose but complete control
   - No reliance on LLM intelligence or framework magic

The "extra friction" in LangGraph isn't a design flaw - it's a different philosophy about who should be responsible for context management. Choose based on your needs:
- **For quick prototypes**: Agno, ADK, or DSPy (simple but LLM-dependent)
- **For production systems**: Pydantic AI (balanced) or LangGraph (maximum control)
- **For type safety**: Pydantic AI (built-in) or LangGraph (can add types to wrappers)

This document explains how these approaches work and their trade-offs.

## The Context Problem

When building agents that analyze codebases, tools often need context about which directory they're operating on. Consider this common tool signature:

```python
def find_all_matching_files(
    directory: str,  # <- This parameter needs to be provided somehow
    pattern: str = "*", 
    respect_gitignore: bool = True,
    include_hidden: bool = False,
    include_subdirs: bool = True
) -> List[str]:
    """Find files matching a pattern in the codebase."""
    # Implementation details...
```

The challenge: How do we provide the `directory` parameter when the agent calls this tool?

## Framework Approaches

### 1. Agno (Phidata) - Context Through Prompts

Agno takes a straightforward approach - it passes tools directly and relies on the prompt to provide context:

```python
# From oss-agent-makers/agno/tech-writer.py
agent = Agent(
    model=model,
    instructions=TECH_WRITER_SYSTEM_PROMPT,
    tools=TOOLS_JSON,  # Direct dictionary of functions
    markdown=False,
)

# Context is provided in the prompt
full_prompt = f"Base directory: {directory_path}\n\n{prompt}"
response = agent.run(full_prompt)
```

**How it works**: After examining Agno's source code, it does NOT automatically inject context from the prompt. The agent passes tools directly to the LLM, which must extract the directory from the prompt context and include it in the tool call arguments. This relies on the LLM being smart enough to understand that when it sees "Base directory: /path" in the prompt, it should use that path when calling tools that need a directory parameter.

### 2. ADK (Google) - Similar Prompt-Based Approach

ADK follows a similar pattern:

```python
# From oss-agent-makers/adk-python/tech-writer.py
tech_writer_agent = Agent(
    name="tech_writer",
    model=model,
    instruction=REACT_SYSTEM_PROMPT,
    tools=list(TOOLS_JSON.values()),  # List of function objects
)

# Context provided in the prompt
full_prompt = f"Base directory: {directory_path}\n\n{prompt}"
```

**How it works**: Like Agno, ADK relies on the LLM understanding the context from the prompt and including the directory in its tool call arguments.

### 3. DSPy - Direct Tool Passing

DSPy uses the original `TOOLS` dictionary (not `TOOLS_JSON`):

```python
# From oss-agent-makers/dspy/tech-writer.py
react_agent = dspy.ReAct(
    TechWriterSignature, 
    tools=list(TOOLS.values()),  # Using TOOLS, not TOOLS_JSON
    max_iters=20
)

# Context in prompt
full_prompt = f"Base directory for analysis: {directory_path}\n\n{prompt_content}"
result = react_agent(prompt=full_prompt)
```

**How it works**: DSPy also relies on the LLM to extract context from the prompt and pass it as arguments to tools.

### 4. Pydantic AI - Explicit Context Injection

Pydantic AI uses a sophisticated dependency injection system:

```python
# From oss-agent-makers/pydantic-ai/tech-writer.py
class AnalysisContext(BaseModel):
    """Context dependencies for the analysis."""
    base_directory: str
    analysis_prompt: str

tech_writer = Agent(
    deps_type=AnalysisContext,
    result_type=str,
    system_prompt=TECH_WRITER_SYSTEM_PROMPT,
)

@tech_writer.tool
async def find_files(
    ctx: RunContext[AnalysisContext],  # Context passed explicitly
    pattern: str = "*", 
    respect_gitignore: bool = True,
    # ... other params
) -> list[str]:
    return find_all_matching_files(
        directory=ctx.deps.base_directory,  # Access context here
        pattern=pattern,
        # ... other args
    )

# When running the agent:
context = AnalysisContext(
    base_directory=directory_path,
    analysis_prompt=prompt
)
result = await tech_writer.run(
    f"Base directory: {directory_path}\n\n{prompt}",
    deps=context,  # Context passed here
    model=model
)
```

**How it works**: After examining Pydantic AI's source code, it uses a **true dependency injection system**:

1. **Agent Definition**: The agent is defined with a `deps_type` (in this case `AnalysisContext`)
2. **Tool Registration**: Tools decorated with `@agent.tool` receive a `RunContext[AnalysisContext]` as their first parameter
3. **Runtime Injection**: When the agent runs, it builds a `RunContext` containing the deps passed to `agent.run()`
4. **Tool Execution**: When a tool is called, Pydantic AI automatically injects the `RunContext` as the first argument

This is different from the other frameworks because:
- The context is **guaranteed** to be available to tools
- It's **type-safe** - the IDE knows what's in `ctx.deps`
- Tools don't rely on the LLM extracting context from prompts
- The directory is still included in the prompt for the LLM's understanding, but tools get it through dependency injection

### 5. LangGraph - Manual Context Binding

LangGraph requires the most explicit approach - creating wrapper functions that bind the context:

```python
# From oss-agent-makers/langgraph/tech-writer.py
# Create tools with bound directory
def find_files(pattern: str = "*", respect_gitignore: bool = True, 
               include_hidden: bool = False, include_subdirs: bool = True) -> List[str]:
    """Find files matching a pattern in the codebase."""
    return find_all_matching_files(
        directory=directory_path,  # Captured from outer scope
        pattern=pattern,
        respect_gitignore=respect_gitignore,
        include_hidden=include_hidden,
        include_subdirs=include_subdirs,
        return_paths_as="str"
    )

def read_file(file_path: str) -> Dict[str, Any]:
    """Read the contents of a specific file."""
    if not Path(file_path).is_absolute():
        file_path = str(Path(directory_path) / file_path)
    return read_file(file_path)

# Create agent with wrapped tools
agent = create_react_agent(
    model=model,
    tools=[find_files, read_file],  # Wrapped functions
)
```

**How it works**: LangGraph doesn't have built-in context management, so we create closure functions that capture the `directory_path` from the surrounding scope.

## Comparison Table

| Framework | Context Passing | Tool Definition | Reliability |
|-----------|----------------|-----------------|-------------|
| Agno | LLM extracts from prompt | Direct functions | Depends on LLM |
| ADK | LLM extracts from prompt | Direct functions | Depends on LLM |
| DSPy | LLM extracts from prompt | Direct functions | Depends on LLM |
| Pydantic AI | Dependency injection | Decorated methods | Guaranteed |
| LangGraph | Manual binding | Wrapper functions | Guaranteed |

## Why The Differences?

After examining the source code of each framework, here's what's actually happening:

### 1. The LLM-Dependent Approach (Agno, ADK, DSPy)

These frameworks pass tools directly to the LLM with their original signatures (including the `directory` parameter). They include the directory in the prompt (e.g., "Base directory: /path") and **rely entirely on the LLM** to:
- Understand that this is the working directory
- Extract this value from the prompt
- Include it as the `directory` parameter when calling tools

**Why it works**: Modern LLMs are smart enough to make this connection most of the time.

**Why it might fail**: 
- Less capable models might not make the connection
- Complex prompts with multiple paths could confuse the LLM
- The LLM might forget to include the directory parameter

### 2. The Dependency Injection Approach (Pydantic AI)

Pydantic AI uses a sophisticated system where:
- Context is defined as a type (`AnalysisContext`)
- Tools receive this context through a `RunContext` parameter
- The framework **automatically injects** the context when calling tools
- The LLM never needs to handle the directory parameter

### 3. The Manual Binding Approach (LangGraph)

LangGraph uses closure functions to:
- Capture the directory from the surrounding scope
- Create new functions that have the directory "baked in"
- Present simpler tool signatures to the LLM (no directory parameter needed)

### The Key Insight

The fundamental difference is **who is responsible for providing the directory parameter**:
- **Agno/ADK/DSPy**: The LLM must extract it from the prompt and pass it
- **Pydantic AI**: The framework injects it automatically
- **LangGraph**: The developer binds it manually

This explains why LangGraph seems to have "extra friction" - it's not relying on LLM intelligence or framework magic, but on explicit developer control.

## Best Practices

1. **For High-Level Frameworks (Agno, ADK, DSPy)**:
   - Ensure your prompt clearly states the context (e.g., "Base directory: /path")
   - Use consistent prompt formatting
   - Test that tools receive correct parameters

2. **For Pydantic AI**:
   - Define clear context types
   - Use the `RunContext` pattern consistently
   - Leverage type hints for better IDE support

3. **For LangGraph**:
   - Create wrapper functions that bind necessary context
   - Document why wrappers are needed
   - Consider creating a factory function for tools:

```python
def create_tools_with_context(directory_path: str) -> List[Callable]:
    """Factory to create tools with bound directory context."""
    def find_files(pattern: str = "*", **kwargs) -> List[str]:
        return find_all_matching_files(directory=directory_path, pattern=pattern, **kwargs)
    
    def read_file(file_path: str) -> Dict[str, Any]:
        if not Path(file_path).is_absolute():
            file_path = str(Path(directory_path) / file_path)
        return read_file(file_path)
    
    return [find_files, read_file]
```

