// Framework list from the CSV
const frameworks = [
    "dspy", "semantic-kernel", "langgraph", "deer-flow", "SuperAGI", 
    "crewai", "potpie", "atomic-agents", "motia", "Archon", 
    "ax", "gpt-researcher", "beeai-framework", "water", "pyspur", 
    "adk-python", "smolagents", "typedai", "AgentStack", "camel", 
    "BaseAI", "AgentIQ", "agents", "agent-zero", "OpenHands", 
    "pydantic-ai", "Agent-S", "rowboat", "n8n", "griptape", 
    "ag2", "eko", "langflow", "AutoGPT", "Flowise", 
    "babyagi", "agno", "pippin", "parlant", "MemGPT", 
    "spinai", "magma", "suna", "julep", "Integuru", 
    "autogen", "dify", "voltagent", "open-cuak", "AgentVerse",
    "No framework"
];

// Mock responses for Overview
const overviewResponses = {
    summary: `## Tech Writer Benchmark Summary

The Tech Writer Benchmark evaluates how different AI agent frameworks handle a common real-world task: analyzing a codebase and generating technical documentation.

**Key Findings:**
- **51 frameworks** evaluated (50 OSS frameworks + "No framework" baseline)
- **Python dominates** with 70% of frameworks, TypeScript follows with 30%
- **Package vs Server split** is roughly 50/50, showing diverse deployment preferences
- **Code complexity** ranges from 50 lines (No framework) to 500+ lines (enterprise frameworks)

**Top Performers:**
1. **LangGraph** - Best balance of features and simplicity
2. **Pydantic-AI** - Excellent type safety and developer experience
3. **DSPy** - Most innovative approach to prompt optimization
4. **CrewAI** - Best multi-agent coordination
5. **AutoGen** - Most comprehensive feature set`,

    leaderboard: `## Framework Leaderboard

### 🏆 Overall Winners by Category

**Best Developer Experience**
1. **Pydantic-AI** - Type-safe, intuitive API, excellent docs
2. **LangGraph** - Visual workflow design, great debugging
3. **Griptape** - Clean abstractions, good defaults

**Most Concise Implementation**
1. **No framework** (50 lines)
2. **Smolagents** (85 lines)
3. **DSPy** (95 lines)

**Best for Production**
1. **LangGraph** - Battle-tested, scalable, observable
2. **AutoGen** - Microsoft-backed, enterprise features
3. **Flowise** - No-code option, easy deployment

**Most Innovative**
1. **DSPy** - Automatic prompt optimization
2. **Agent-S** - Novel search strategies
3. **Archon** - Interesting architecture patterns

**Best Multi-Agent Support**
1. **CrewAI** - Purpose-built for teams
2. **AutoGen** - Flexible agent conversations
3. **AgentVerse** - Simulation capabilities`,

    method: `## Evaluation Methodology

### The Task
Each framework implements the same "Tech Writer" agent that:
1. Accepts a GitHub repo URL or local directory
2. Analyzes the codebase structure
3. Generates comprehensive technical documentation
4. Outputs in a specified format (Markdown/JSON)

### Evaluation Criteria

**Functional Requirements**
- ✅ Supports both local and GitHub repos
- ✅ Configurable output formats
- ✅ Handles multiple file types
- ✅ Produces structured documentation

**Code Quality Metrics**
- **Lines of Code**: Excluding imports and comments
- **Complexity**: Cyclomatic complexity score
- **Dependencies**: Number of external packages
- **Type Safety**: Static typing coverage

**Developer Experience**
- **Setup Time**: From zero to working agent
- **Documentation**: Quality and completeness
- **API Design**: Intuitiveness and consistency
- **Error Handling**: Clarity of error messages

**Performance**
- **Execution Time**: For standard test repo
- **Token Efficiency**: LLM tokens used
- **Memory Usage**: Peak RAM consumption`,

    future: `## Future Directions

### Planned Improvements

**Q1 2025**
- Add streaming support evaluation
- Include cost analysis per framework
- Benchmark on larger codebases
- Add multi-language support tests

**Q2 2025**
- Evaluation of vision capabilities
- RAG implementation comparisons
- Custom tool creation ease
- Production deployment guides

### Community Contributions

We welcome contributions to expand the benchmark:
- **New Frameworks**: Submit PRs to add frameworks
- **Test Cases**: Suggest challenging scenarios
- **Metrics**: Propose new evaluation criteria
- **Visualizations**: Improve result presentation

### Research Applications

This benchmark enables:
- Framework selection for specific use cases
- Understanding of design patterns in AI agents
- Identification of common implementation challenges
- Tracking ecosystem evolution over time

Visit [bench.makingaiaagents.com](https://bench.makingaiaagents.com) for live results.`
};

// Mock framework-specific data
const frameworkData = {
    "langgraph": {
        summary: `## LangGraph Implementation

LangGraph provides a **graph-based approach** to building AI agents, making complex workflows visual and maintainable.

**Key Characteristics:**
- 📊 Visual workflow representation
- 🔄 Built-in state management
- 🎯 Explicit control flow
- 🔍 Excellent debugging tools

**Implementation Stats:**
- **Lines of Code**: 187
- **Complexity**: Medium
- **Dependencies**: 5 (minimal)
- **Setup Time**: 15 minutes`,

        llms: `## LLM Integration in LangGraph

**Supported Providers:**
- OpenAI (GPT-3.5/4)
- Anthropic (Claude)
- Google (Gemini)
- Azure OpenAI
- Any LangChain-compatible model

**Configuration Example:**
\`\`\`python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    max_tokens=2000
)

graph = StateGraph(State)
graph.add_node("analyzer", lambda x: analyze_code(x, llm))
\`\`\`

**Unique Features:**
- Automatic retry logic
- Token counting per node
- Streaming support built-in
- Easy model swapping`,

        tools: `## Tools & Functions

LangGraph uses a **node-based** tool system:

**Built-in Tools:**
- File system operations
- Web scraping
- Code parsing
- Git operations

**Tool Definition:**
\`\`\`python
@tool
def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    return Path(path).read_text()

# Add to graph
graph.add_node("reader", read_file)
\`\`\`

**Tool Chaining:**
- Automatic output passing
- Error boundaries per tool
- Conditional tool execution
- Parallel tool runs`,

        memory: `## Memory & State Management

**State Definition:**
\`\`\`python
class State(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    repo_url: str
    file_contents: dict[str, str]
    analysis: str
\`\`\`

**Memory Features:**
- ✅ Conversation history
- ✅ Intermediate results
- ✅ Checkpointing support
- ✅ State persistence

**Advanced Patterns:**
- Selective state updates
- State branching for parallel paths
- Redis backend for scaling
- Time-travel debugging`,

        other: `## Other Notable Features

**Observability:**
- LangSmith integration
- Visual execution traces
- Step-by-step debugging
- Performance profiling

**Deployment:**
- LangServe for APIs
- Async support throughout
- Horizontal scaling ready
- Docker-friendly

**Community:**
- Active Discord
- Regular updates
- Good documentation
- Growing ecosystem

**Limitations:**
- Learning curve for graphs
- Verbose for simple tasks
- Limited built-in agents`,

        code: `# LangGraph Tech Writer Implementation

from typing import TypedDict, Annotated, Sequence
import operator
from pathlib import Path
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import git

# Define the state structure
class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    repo_path: str
    file_tree: dict
    analysis: str
    output_format: str

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Define tools
@tool
def clone_repo(repo_url: str) -> str:
    """Clone a GitHub repository to local storage."""
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    local_path = f"/tmp/{repo_name}"
    
    if Path(local_path).exists():
        return local_path
    
    git.Repo.clone_from(repo_url, local_path)
    return local_path

@tool
def analyze_file_structure(repo_path: str) -> dict:
    """Analyze the repository file structure."""
    structure = {}
    repo = Path(repo_path)
    
    for file_path in repo.rglob('*'):
        if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
            relative_path = file_path.relative_to(repo)
            structure[str(relative_path)] = {
                'size': file_path.stat().st_size,
                'extension': file_path.suffix
            }
    
    return structure

# Define nodes
def setup_node(state: State) -> State:
    """Initialize the analysis process."""
    messages = state['messages']
    last_message = messages[-1].content
    
    # Extract repo URL from message
    import re
    url_match = re.search(r'https://github\.com/[\w-]+/[\w-]+', last_message)
    
    if url_match:
        state['repo_path'] = clone_repo.invoke({"repo_url": url_match.group()})
    
    return state

def analyze_node(state: State) -> State:
    """Analyze the repository structure."""
    if 'repo_path' in state:
        state['file_tree'] = analyze_file_structure.invoke({"repo_path": state['repo_path']})
    
    return state

def generate_docs_node(state: State) -> State:
    """Generate technical documentation."""
    prompt = f"""
    Analyze this repository structure and generate comprehensive technical documentation:
    
    Repository: {state.get('repo_path', 'Unknown')}
    Files: {state.get('file_tree', {})}
    
    Generate documentation including:
    1. Project overview
    2. Architecture description
    3. Setup instructions
    4. API documentation (if applicable)
    5. Usage examples
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    state['analysis'] = response.content
    state['messages'].append(response)
    
    return state

def format_output_node(state: State) -> State:
    """Format the output according to preferences."""
    if state.get('output_format') == 'json':
        # Convert to JSON format
        import json
        state['analysis'] = json.dumps({
            'documentation': state['analysis'],
            'metadata': {
                'repo': state.get('repo_path'),
                'files_analyzed': len(state.get('file_tree', {}))
            }
        }, indent=2)
    
    return state

# Build the graph
def create_tech_writer_graph():
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("setup", setup_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("generate", generate_docs_node)
    graph.add_node("format", format_output_node)
    
    # Add edges
    graph.set_entry_point("setup")
    graph.add_edge("setup", "analyze")
    graph.add_edge("analyze", "generate")
    graph.add_edge("generate", "format")
    graph.add_edge("format", END)
    
    return graph.compile()

# Usage
if __name__ == "__main__":
    # Create the agent
    tech_writer = create_tech_writer_graph()
    
    # Run analysis
    initial_state = {
        "messages": [HumanMessage(content="Analyze https://github.com/langchain-ai/langgraph")],
        "output_format": "markdown"
    }
    
    result = tech_writer.invoke(initial_state)
    print(result['analysis'])`
    },
    
    "pydantic-ai": {
        summary: `## Pydantic-AI Implementation

Pydantic-AI brings **type safety** and **structured outputs** to AI agents, leveraging Pydantic's validation.

**Key Characteristics:**
- 🔒 Full type safety with Python types
- 📋 Structured output validation
- 🚀 Minimal boilerplate
- 🎯 Schema-first design

**Implementation Stats:**
- **Lines of Code**: 142
- **Complexity**: Low
- **Dependencies**: 3 (minimal)
- **Setup Time**: 10 minutes`,

        llms: `## LLM Integration in Pydantic-AI

**Type-Safe Configuration:**
\`\`\`python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

model = OpenAIModel(
    'gpt-4',
    api_key=os.environ['OPENAI_API_KEY']
)

agent = Agent(
    model=model,
    system_prompt="You are a technical documentation expert."
)
\`\`\`

**Multi-Model Support:**
- OpenAI GPT series
- Anthropic Claude
- Local models via Ollama
- Custom model adapters

**Unique Features:**
- Automatic output parsing
- Type-validated responses
- Retry with validation
- Cost tracking built-in`,

        tools: `## Tools & Functions

**Typed Tool Definition:**
\`\`\`python
from pydantic_ai import Tool
from pydantic import BaseModel

class FileContent(BaseModel):
    path: str
    content: str
    
@agent.tool
async def read_file(ctx: Context, path: str) -> FileContent:
    """Read file with full type safety."""
    content = Path(path).read_text()
    return FileContent(path=path, content=content)
\`\`\`

**Tool Features:**
- Full async support
- Automatic validation
- Context injection
- Error handling
- Dependency injection`,

        memory: `## Memory & State Management

**Structured Context:**
\`\`\`python
class AnalysisContext(BaseModel):
    repo_url: str
    files_analyzed: List[str] = []
    findings: Dict[str, Any] = {}
    
agent = Agent(
    model=model,
    context_type=AnalysisContext
)
\`\`\`

**State Features:**
- Type-safe context
- Automatic persistence
- Validation on updates
- Immutable by default
- Transaction support`,

        other: `## Other Notable Features

**Developer Experience:**
- IntelliSense everywhere
- Compile-time checks
- Self-documenting code
- Excellent error messages

**Testing:**
- Built-in test utilities
- Mock model support
- Snapshot testing
- Deterministic mode

**Performance:**
- Minimal overhead
- Efficient validation
- Streaming support
- Batch processing

**Limitations:**
- Newer framework
- Smaller ecosystem
- Limited agent types`,

        code: `# Pydantic-AI Tech Writer Implementation

from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
import aiofiles
import asyncio
from datetime import datetime

# Define structured models
class FileInfo(BaseModel):
    path: str
    size: int
    extension: str
    last_modified: datetime

class RepoAnalysis(BaseModel):
    name: str
    description: str
    structure: Dict[str, List[FileInfo]]
    total_files: int
    primary_language: Optional[str]
    
class Documentation(BaseModel):
    title: str
    overview: str
    architecture: str
    setup_instructions: List[str]
    api_reference: Optional[Dict[str, Any]]
    examples: List[str]
    
class TechWriterContext(BaseModel):
    repo_path: Path
    output_format: str = "markdown"
    files_analyzed: List[str] = Field(default_factory=list)
    
# Initialize the agent
model = OpenAIModel('gpt-4')

tech_writer = Agent(
    model=model,
    system_prompt="""You are an expert technical writer. 
    Analyze codebases and create comprehensive, clear documentation.
    Focus on architecture, setup, and usage examples.""",
    context_type=TechWriterContext,
    result_type=Documentation
)

# Define tools
@tech_writer.tool
async def scan_repository(ctx: RunContext[TechWriterContext]) -> RepoAnalysis:
    """Scan repository structure and gather metadata."""
    repo_path = ctx.context.repo_path
    
    structure = {}
    total_files = 0
    extensions = []
    
    for file_path in repo_path.rglob('*'):
        if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
            relative = file_path.relative_to(repo_path)
            parent = str(relative.parent)
            
            if parent not in structure:
                structure[parent] = []
                
            structure[parent].append(FileInfo(
                path=str(relative),
                size=file_path.stat().st_size,
                extension=file_path.suffix,
                last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
            ))
            
            total_files += 1
            if file_path.suffix:
                extensions.append(file_path.suffix)
    
    # Determine primary language
    from collections import Counter
    ext_counts = Counter(extensions)
    primary_ext = ext_counts.most_common(1)[0][0] if ext_counts else None
    
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript', 
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.go': 'Go'
    }
    
    return RepoAnalysis(
        name=repo_path.name,
        description=f"Repository with {total_files} files",
        structure=structure,
        total_files=total_files,
        primary_language=language_map.get(primary_ext)
    )

@tech_writer.tool  
async def read_file_content(
    ctx: RunContext[TechWriterContext], 
    file_path: str
) -> str:
    """Read specific file content for analysis."""
    full_path = ctx.context.repo_path / file_path
    
    try:
        async with aiofiles.open(full_path, 'r') as f:
            content = await f.read()
            ctx.context.files_analyzed.append(file_path)
            return content
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"

@tech_writer.tool
async def find_entry_points(ctx: RunContext[TechWriterContext]) -> List[str]:
    """Find main entry points in the codebase."""
    entry_points = []
    repo_path = ctx.context.repo_path
    
    # Common entry point patterns
    patterns = ['main.py', 'app.py', 'index.js', 'index.ts', 'server.py', 'cli.py']
    
    for pattern in patterns:
        for file_path in repo_path.rglob(pattern):
            if file_path.is_file():
                entry_points.append(str(file_path.relative_to(repo_path)))
    
    # Check for package.json scripts
    package_json = repo_path / 'package.json'
    if package_json.exists():
        import json
        with open(package_json) as f:
            data = json.load(f)
            if 'scripts' in data:
                entry_points.append("package.json (see scripts)")
    
    return entry_points

# Main function
async def analyze_repository(repo_path: str, output_format: str = "markdown") -> str:
    """Analyze a repository and generate documentation."""
    
    context = TechWriterContext(
        repo_path=Path(repo_path),
        output_format=output_format
    )
    
    # Run the agent
    result = await tech_writer.run(
        "Analyze this repository and create comprehensive technical documentation. "
        "Include overview, architecture, setup instructions, and usage examples.",
        context=context
    )
    
    # Format output
    if output_format == "markdown":
        return format_as_markdown(result.data)
    elif output_format == "json":
        return result.data.model_dump_json(indent=2)
    else:
        return str(result.data)

def format_as_markdown(doc: Documentation) -> str:
    """Convert Documentation to markdown format."""
    md = f"# {doc.title}\\n\\n"
    md += f"## Overview\\n{doc.overview}\\n\\n"
    md += f"## Architecture\\n{doc.architecture}\\n\\n"
    md += f"## Setup Instructions\\n"
    for i, instruction in enumerate(doc.setup_instructions, 1):
        md += f"{i}. {instruction}\\n"
    md += "\\n"
    
    if doc.api_reference:
        md += "## API Reference\\n"
        for endpoint, details in doc.api_reference.items():
            md += f"### {endpoint}\\n{details}\\n\\n"
    
    if doc.examples:
        md += "## Examples\\n"
        for example in doc.examples:
            md += f"\`\`\`\\n{example}\\n\`\`\`\\n\\n"
    
    return md

# Usage
if __name__ == "__main__":
    result = asyncio.run(
        analyze_repository("/path/to/repo", "markdown")
    )
    print(result)`
    },

    // Add more frameworks with similar structure...
    "No framework": {
        summary: `## No Framework Implementation

The **baseline implementation** using just standard Python libraries and direct API calls.

**Key Characteristics:**
- 🎯 Zero dependencies (except OpenAI SDK)
- 📝 Direct, readable code
- 🚀 Minimal abstraction
- 💡 Great for learning

**Implementation Stats:**
- **Lines of Code**: 67
- **Complexity**: Very Low
- **Dependencies**: 1 (openai)
- **Setup Time**: 5 minutes`,

        llms: `## Direct OpenAI Integration

**Simple Setup:**
\`\`\`python
from openai import OpenAI

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def analyze_code(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a tech writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content
\`\`\`

**Pros:**
- Direct control
- No abstraction overhead
- Easy to debug
- Minimal learning curve

**Cons:**
- No built-in retry
- Manual error handling
- No streaming support
- Basic functionality only`,

        tools: `## Manual Tool Implementation

**File Reading:**
\`\`\`python
def read_files(directory: str) -> dict:
    files = {}
    for path in Path(directory).rglob('*'):
        if path.is_file():
            try:
                files[str(path)] = path.read_text()
            except:
                files[str(path)] = "<binary file>"
    return files
\`\`\`

**No Framework Means:**
- Write your own tools
- Handle errors manually
- No tool chaining
- Full control over logic`,

        memory: `## Basic State Management

**Simple Dictionary:**
\`\`\`python
state = {
    'files': {},
    'analysis': '',
    'history': []
}

# Manual updates
state['files'] = read_files(repo_path)
state['analysis'] = analyze_code(prompt)
state['history'].append(result)
\`\`\`

**Limitations:**
- No persistence
- Manual management
- No validation
- Memory leaks possible`,

        other: `## Considerations

**When to Use:**
- Learning/prototypes
- Simple scripts
- Full control needed
- Minimal dependencies

**When to Avoid:**
- Production systems
- Complex workflows
- Team projects
- Need advanced features

**Migration Path:**
Easy to migrate to any framework since it's just standard Python.`,

        code: `# No Framework Tech Writer Implementation

import os
import json
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def read_repository(repo_path: str) -> Dict[str, str]:
    """Read all text files from repository."""
    files = {}
    repo = Path(repo_path)
    
    # Common code file extensions
    code_extensions = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h'}
    doc_extensions = {'.md', '.txt', '.rst'}
    
    for file_path in repo.rglob('*'):
        if file_path.is_file() and file_path.suffix in (code_extensions | doc_extensions):
            try:
                relative_path = file_path.relative_to(repo)
                files[str(relative_path)] = file_path.read_text(encoding='utf-8')
            except Exception as e:
                console.log(\`Error reading \${file_path}: \${e}\`)
                
    return files

def create_prompt(files: Dict[str, str]) -> str:
    """Create analysis prompt with file contents."""
    prompt = "Analyze this codebase and create technical documentation:\\n\\n"
    
    # Add file structure
    prompt += "File Structure:\\n"
    for file_path in sorted(files.keys()):
        prompt += f"- {file_path}\\n"
    
    prompt += "\\n---\\n\\n"
    
    # Add key files content (limit to prevent token overflow)
    important_files = ['README.md', 'setup.py', 'package.json', 'main.py', 'index.js']
    
    for file_path, content in files.items():
        if any(name in file_path for name in important_files):
            prompt += f"File: {file_path}\\n\`\`\`\\n{content[:1000]}...\\n\`\`\`\\n\\n"
    
    prompt += """
Please provide:
1. Project Overview
2. Architecture Description  
3. Setup Instructions
4. API Documentation (if applicable)
5. Usage Examples
"""
    
    return prompt

def generate_documentation(repo_path: str, output_format: str = "markdown") -> str:
    """Main function to analyze repository and generate docs."""
    
    # Read repository files
    print(f"Reading repository: {repo_path}")
    files = read_repository(repo_path)
    print(f"Found {len(files)} files")
    
    # Create analysis prompt
    prompt = create_prompt(files)
    
    # Call OpenAI API
    print("Generating documentation...")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert technical writer. Create clear, comprehensive documentation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=4000
        )
        
        documentation = response.choices[0].message.content
        
        # Format output if needed
        if output_format == "json":
            return json.dumps({
                "documentation": documentation,
                "metadata": {
                    "repo_path": repo_path,
                    "files_analyzed": len(files),
                    "model": "gpt-4"
                }
            }, indent=2)
        
        return documentation
        
    except Exception as e:
        return f"Error generating documentation: {str(e)}"

# Usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tech_writer.py <repo_path> [output_format]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    
    result = generate_documentation(repo_path, output_format)
    
    # Save to file
    output_file = "documentation.md" if output_format == "markdown" else "documentation.json"
    with open(output_file, 'w') as f:
        f.write(result)
    
    print(f"Documentation saved to {output_file}")`
    }
};

// Add basic data for other frameworks (you can expand these)
frameworks.forEach(framework => {
    if (!frameworkData[framework]) {
        frameworkData[framework] = {
            summary: `## ${framework} Implementation\n\nThis framework provides tools for building AI agents with focus on ease of use and flexibility.\n\n**Key Features:**\n- Agent orchestration\n- Tool integration\n- Memory management\n- LLM abstraction`,
            llms: `## LLM Support\n\nSupports major LLM providers through a unified interface.`,
            tools: `## Tools & Functions\n\nProvides a tool system for extending agent capabilities.`,
            memory: `## Memory Management\n\nIncludes memory features for maintaining context.`,
            other: `## Additional Features\n\nVarious other features for production use.`,
            code: `# ${framework} implementation\n\n# Code example would go here\nprint("Implementation example for ${framework}")`
        };
    }
});

// Mock chat responses
const chatResponses = {
    "What's the simplest implementation available?": `The **simplest implementation** is the **"No framework"** approach with just 67 lines of code!

It uses only the OpenAI SDK and standard Python libraries. Perfect for:
- Learning how agents work
- Quick prototypes  
- Minimal dependencies
- Full control

However, **Smolagents** (85 lines) and **DSPy** (95 lines) offer more features while staying concise.`,

    "Which framework offers the best type safety?": `**Pydantic-AI** leads in type safety! 🏆

It leverages Pydantic's validation for:
- Full static typing support
- Runtime validation
- Structured outputs
- Type-safe tool definitions

**Runners up:**
- **TypeScript frameworks** (ax, agents, BaseAI) - compile-time safety
- **Griptape** - good Python typing
- **LangGraph** - TypedDict state management`,

    "Compare LangGraph and Pydantic-AI": `## LangGraph vs Pydantic-AI

**LangGraph** 📊
- Graph-based workflows
- Visual debugging
- 187 lines of code
- Better for complex flows
- Steeper learning curve

**Pydantic-AI** 🔒
- Type-safe throughout
- Structured outputs
- 142 lines of code
- Better for data validation
- Easier to learn

**Choose LangGraph if:** You need complex multi-step workflows
**Choose Pydantic-AI if:** You want type safety and structured data`
};