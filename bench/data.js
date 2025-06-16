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

        code: '# LangGraph Tech Writer Implementation\n\nfrom typing import TypedDict, Annotated, Sequence\nimport operator\nfrom pathlib import Path\nfrom langgraph.graph import StateGraph, END\nfrom langchain_core.messages import BaseMessage, HumanMessage, AIMessage\nfrom langchain_openai import ChatOpenAI\nfrom langchain_core.tools import tool\nimport git\n\n# Define the state structure\nclass State(TypedDict):\n    messages: Annotated[Sequence[BaseMessage], operator.add]\n    repo_path: str\n    file_tree: dict\n    analysis: str\n    output_format: str\n\n# Initialize LLM\nllm = ChatOpenAI(model="gpt-4", temperature=0)\n\n# Define tools\n@tool\ndef clone_repo(repo_url: str) -> str:\n    """Clone a GitHub repository to local storage."""\n    repo_name = repo_url.split(\'/\')[-1].replace(\'.git\', \'\')\n    local_path = f"/tmp/{repo_name}"\n    \n    if Path(local_path).exists():\n        return local_path\n    \n    git.Repo.clone_from(repo_url, local_path)\n    return local_path\n\n@tool\ndef analyze_file_structure(repo_path: str) -> dict:\n    """Analyze the repository file structure."""\n    structure = {}\n    repo = Path(repo_path)\n    \n    for file_path in repo.rglob(\'*\'):\n        if file_path.is_file() and not any(part.startswith(\'.\') for part in file_path.parts):\n            relative_path = file_path.relative_to(repo)\n            structure[str(relative_path)] = {\n                \'size\': file_path.stat().st_size,\n                \'extension\': file_path.suffix\n            }\n    \n    return structure\n\n# Define nodes\ndef setup_node(state: State) -> State:\n    """Initialize the analysis process."""\n    messages = state[\'messages\']\n    last_message = messages[-1].content\n    \n    # Extract repo URL from message\n    import re\n    url_match = re.search(r\'https://github\\.com/[\\w-]+/[\\w-]+\', last_message)\n    \n    if url_match:\n        state[\'repo_path\'] = clone_repo.invoke({"repo_url": url_match.group()})\n    \n    return state\n\ndef analyze_node(state: State) -> State:\n    """Analyze the repository structure."""\n    if \'repo_path\' in state:\n        state[\'file_tree\'] = analyze_file_structure.invoke({"repo_path": state[\'repo_path\']})\n    \n    return state\n\ndef generate_docs_node(state: State) -> State:\n    """Generate technical documentation."""\n    prompt = f"""\n    Analyze this repository structure and generate comprehensive technical documentation:\n    \n    Repository: {state.get(\'repo_path\', \'Unknown\')}\n    Files: {state.get(\'file_tree\', {})}\n    \n    Generate documentation including:\n    1. Project overview\n    2. Architecture description\n    3. Setup instructions\n    4. API documentation (if applicable)\n    5. Usage examples\n    """\n    \n    response = llm.invoke([HumanMessage(content=prompt)])\n    state[\'analysis\'] = response.content\n    state[\'messages\'].append(response)\n    \n    return state\n\ndef format_output_node(state: State) -> State:\n    """Format the output according to preferences."""\n    if state.get(\'output_format\') == \'json\':\n        # Convert to JSON format\n        import json\n        state[\'analysis\'] = json.dumps({\n            \'documentation\': state[\'analysis\'],\n            \'metadata\': {\n                \'repo\': state.get(\'repo_path\'),\n                \'files_analyzed\': len(state.get(\'file_tree\', {}))\n            }\n        }, indent=2)\n    \n    return state\n\n# Build the graph\ndef create_tech_writer_graph():\n    graph = StateGraph(State)\n    \n    # Add nodes\n    graph.add_node("setup", setup_node)\n    graph.add_node("analyze", analyze_node)\n    graph.add_node("generate", generate_docs_node)\n    graph.add_node("format", format_output_node)\n    \n    # Add edges\n    graph.set_entry_point("setup")\n    graph.add_edge("setup", "analyze")\n    graph.add_edge("analyze", "generate")\n    graph.add_edge("generate", "format")\n    graph.add_edge("format", END)\n    \n    return graph.compile()\n\n# Usage\nif __name__ == "__main__":\n    # Create the agent\n    tech_writer = create_tech_writer_graph()\n    \n    # Run analysis\n    initial_state = {\n        "messages": [HumanMessage(content="Analyze https://github.com/langchain-ai/langgraph")],\n        "output_format": "markdown"\n    }\n    \n    result = tech_writer.invoke(initial_state)\n    print(result[\'analysis\'])'
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

        code: 'File content too long - truncated for display'
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

        code: 'File content too long - truncated for display'
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