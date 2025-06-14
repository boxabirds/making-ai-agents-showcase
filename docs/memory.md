# State/Memory Management in Python Agent Frameworks

Based on examination of the actual source code, here's how each framework manages state during agent execution.


## Key Insights

1. **ADK-Python** is the only framework with **explicit multi-user session management** built into its core architecture, making it clear when state persists across runs.

2. **Agno** has the richest memory model with user memories, session summaries, and database persistence options built-in.

3. **Pydantic AI** and **LangGraph** use functional/graph-based approaches where state flows through the execution rather than being stored in mutable objects.

4. **DSPy** focuses on trajectory/trace storage for its optimization capabilities rather than traditional conversation memory.

5. **My Custom "Bare Metal" Python implementation** gives complete control but requires manual implementation of any persistence or session management.

## Summary Comparison

| Framework | State Storage | Persistence | Multi-User | Key Feature |
|-----------|--------------|-------------|------------|-------------|
| **Bare Metal** | Instance list | None | No | Full control |
| **ADK-Python** | Session hierarchy | Pluggable | Yes | Explicit sessions |
| **Pydantic AI** | Graph state | Run-scoped | No | Immutable deps |
| **Agno** | Rich memory model | Database | Yes | User memories |
| **DSPy** | Trajectory dict | None | No | Optimization traces |
| **LangGraph** | Message state | Optional | No | Graph flow |

## 1. Bare Metal Implementation
**Source examined**: `tech-writer.py` lines 29, 145-152, 185, 256-261
- **State Storage**: `self.memory = []` - explicit list in the agent instance
- **What's Stored**: List of message dictionaries with role/content
- **Persistence**: None - memory exists only during execution
- **Key Pattern**: Direct list manipulation, developer has full control

```python
# From noframework/python/tech-writer.py
class TechWriterReActAgent:
    def __init__(self, model_name="openai/gpt-4.1-mini", base_url=None):
        self.memory = []  # Explicit memory list
        self.final_answer = None
        
    def initialise_memory(self, prompt, directory):
        self.memory = [{"role": "system", "content": self.system_prompt}]
        self.memory.append({"role": "user", "content": f"Base directory: {directory}\n\n{prompt}"})
```

## 2. ADK-Python (Google's Agent Development Kit)
**Source examined**: `InMemorySessionService.py`, `InMemoryRunner` in `runners.py`
- **State Storage**: Session-based with three levels:
  - `self.sessions[app_name][user_id][session_id]` - session events
  - `self.user_state[app_name][user_id]` - user-level state
  - `self.app_state[app_name]` - app-level state  
- **What's Stored**: Events list, session metadata, state dictionaries
- **Persistence**: InMemoryRunner loses state on exit, but architecture supports persistent backends
- **Key Pattern**: Explicit session management with `session_id` and `user_id`

```python
# From ADK's InMemorySessionService
class InMemorySessionService(BaseSessionService):
    def __init__(self):
        # A map from app name to a map from user ID to a map from session ID to session
        self.sessions: dict[str, dict[str, dict[str, Session]]] = {}
        # A map from app name to a map from user ID to a map from key to the value
        self.user_state: dict[str, dict[str, dict[str, Any]]] = {}
        # A map from app name to a map from key to the value
        self.app_state: dict[str, dict[str, Any]] = {}
```

## 3. Pydantic AI
**Source examined**: `agent.py`, `_agent_graph.py`
- **State Storage**: 
  - `GraphAgentState` dataclass with `message_history`, `usage`, `retries`, `run_step`
  - Dependencies passed via `GraphAgentDeps` with `user_deps`
- **What's Stored**: Message history, usage stats, retry counts, dependencies
- **Persistence**: State exists only during run execution
- **Key Pattern**: Immutable dependencies via context injection, state in graph traversal

```python
# From Pydantic AI's _agent_graph.py
@dataclasses.dataclass
class GraphAgentState:
    """State kept across the execution of the agent graph."""
    message_history: list[_messages.ModelMessage]
    usage: _usage.Usage
    retries: int
    run_step: int
```

## 4. Agno (Phidata)
**Source examined**: `agent.py`, `memory/agent.py`
- **State Storage**:
  - `AgentMemory` class with `runs`, `messages`, `memories`, `summary`
  - Optional database storage via `MemoryDb`
  - Session state stored as `session_state: Dict[str, Any]`
- **What's Stored**: Full conversation runs, user memories, session summaries
- **Persistence**: Supports database persistence for memories and sessions
- **Key Pattern**: Rich memory model with summaries and user-specific memories

```python
# From Agno's memory/agent.py
class AgentMemory(BaseModel):
    # Runs between the user and agent
    runs: List[AgentRun] = []
    # List of messages sent to the model
    messages: List[Message] = []
    # Summary of the session
    summary: Optional[SessionSummary] = None
    # Create and store personalized memories for this user
    create_user_memories: bool = False
    # MemoryDb to store personalized memories
    db: Optional[MemoryDb] = None
```

## 5. DSPy
**Source examined**: `predict/react.py`
- **State Storage**: `trajectory = {}` dictionary built during execution
- **What's Stored**: Thoughts, tool names, tool args, observations indexed by step
- **Persistence**: None - trajectory exists only during run
- **Key Pattern**: Trace-based approach for optimization, state as trajectory

```python
# From DSPy's predict/react.py
def forward(self, **input_args):
    trajectory = {}
    for idx in range(max_iters):
        # Build trajectory step by step
        trajectory[f"thought_{idx}"] = pred.next_thought
        trajectory[f"tool_name_{idx}"] = pred.next_tool_name
        trajectory[f"tool_args_{idx}"] = pred.next_tool_args
        trajectory[f"observation_{idx}"] = self.tools[pred.next_tool_name](**pred.next_tool_args)
```

## 6. LangGraph
**Source examined**: `chat_agent_executor.py`, `graph/state.py`
- **State Storage**: 
  - `AgentState` TypedDict with `messages` field using `add_messages` reducer
  - State flows through graph nodes
- **What's Stored**: Message sequences with automatic aggregation
- **Persistence**: Optional via `checkpointer` parameter
- **Key Pattern**: Message-centric state with graph-based flow

```python
# From LangGraph's chat_agent_executor.py
class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps
```
