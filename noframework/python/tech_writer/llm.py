"""
LLM interface for tool calling.

Provides a unified interface for LLM interactions with:
- Tool registration (OpenAI function calling format)
- Tool execution loop
- Response parsing
- Multi-provider support (OpenAI, OpenRouter)
- Cost tracking (OpenRouter)
"""

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional

from openai import OpenAI

from tech_writer.logging import (
    log_llm_request,
    log_llm_response,
    log_tool_call,
    log_tool_result,
    logger,
)


# Constants
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_APP_NAME = "tech_writer"
DEFAULT_APP_URL = "https://github.com/user/tech_writer"



@dataclass
class UsageStats:
    """Token and cost statistics for a single LLM call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: Optional[float] = None
    cached_tokens: int = 0
    cache_discount: float = 0.0
    generation_id: Optional[str] = None


@dataclass
class CostSummary:
    """Cumulative cost statistics for a pipeline run."""

    total_cost_usd: float = 0.0
    total_tokens: int = 0
    total_calls: int = 0
    provider: str = ""
    model: str = ""
    calls: list[UsageStats] = field(default_factory=list)


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    provider: Literal["openai", "openrouter"]
    base_url: Optional[str]
    api_key: str
    default_headers: dict[str, str]

    @classmethod
    def from_provider(
        cls,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        app_name: str = DEFAULT_APP_NAME,
        app_url: str = DEFAULT_APP_URL,
    ) -> "ProviderConfig":
        """
        Factory method to create config from provider name.

        Args:
            provider: Provider name ("openai" or "openrouter")
            api_key: API key (or from environment)
            base_url: Override base URL
            app_name: App name for OpenRouter dashboard
            app_url: App URL for OpenRouter HTTP-Referer header

        Returns:
            ProviderConfig instance

        Raises:
            ValueError: If provider is unknown or API key is missing
        """
        if provider == "openrouter":
            resolved_key = api_key or os.environ.get("OPENROUTER_API_KEY")
            if not resolved_key:
                raise ValueError(
                    "OpenRouter API key required. Set OPENROUTER_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            return cls(
                provider="openrouter",
                base_url=base_url or OPENROUTER_BASE_URL,
                api_key=resolved_key,
                default_headers={
                    "HTTP-Referer": app_url,
                    "X-Title": app_name,
                },
            )
        elif provider == "openai":
            resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
            if not resolved_key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            return cls(
                provider="openai",
                base_url=base_url,
                api_key=resolved_key,
                default_headers={},
            )
        else:
            raise ValueError(
                f"Unknown provider: {provider}. Valid providers: openai, openrouter"
            )


class CostTracker:
    """Tracks cumulative costs across LLM calls.

    Cost data comes directly from OpenRouter's response.usage.cost field
    when extra_body={'usage': {'include': True}} is set.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize cost tracker.

        Args:
            enabled: Whether cost tracking is enabled
        """
        self.enabled = enabled
        self.total_cost: float = 0.0
        self.total_tokens: int = 0
        self.calls: list[UsageStats] = []

    def record_call(self, usage: UsageStats) -> None:
        """
        Record a call's usage statistics.

        Args:
            usage: Usage stats (including cost from response)
        """
        if not self.enabled:
            return

        # Accumulate totals
        if usage.cost_usd is not None:
            self.total_cost += usage.cost_usd
        self.total_tokens += usage.total_tokens
        self.calls.append(usage)

    def get_summary(self, provider: str, model: str) -> CostSummary:
        """
        Return cumulative cost statistics.

        Args:
            provider: Provider name
            model: Model name

        Returns:
            CostSummary with accumulated statistics
        """
        return CostSummary(
            total_cost_usd=self.total_cost,
            total_tokens=self.total_tokens,
            total_calls=len(self.calls),
            provider=provider,
            model=model,
            calls=list(self.calls),
        )


# Type for tool functions
ToolFunction = Callable[..., Any]


# Tool definitions in OpenAI format
EXPLORATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files matching a glob pattern in the repository. Use this to explore the directory structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '**/*.py', 'src/*.js', '*.md')",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search from (default: repo root)",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file's content. Use this to examine code and understand implementation details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to repository root",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Optional start line (1-indexed)",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Optional end line (inclusive)",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_symbols",
            "description": "Get all symbols (functions, classes, methods) defined in a file. Use this to understand file structure without reading the entire file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path",
                    },
                    "kind": {
                        "type": "string",
                        "enum": ["function", "class", "method"],
                        "description": "Filter by symbol type",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_imports",
            "description": "Get all imports in a file. Use this to understand dependencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_definition",
            "description": "Find where a symbol (function, class) is defined. Use this to trace code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Symbol name to find",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_references",
            "description": "Find all usages of a symbol. Use this to understand how code is used.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Symbol name to find",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_structure",
            "description": "Get structural overview of a file (imports, classes with methods, functions). Gives a complete picture of the file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_text",
            "description": "Search for text across all files you've read. Use this to find specific patterns or code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (regex supported)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish_exploration",
            "description": "Signal that you have gathered enough information to proceed with documentation. Call this when you understand the codebase well enough.",
            "parameters": {
                "type": "object",
                "properties": {
                    "understanding": {
                        "type": "string",
                        "description": "Summary of what you've learned about the codebase",
                    },
                },
                "required": ["understanding"],
            },
        },
    },
]


def get_tool_definitions() -> list[dict]:
    """Get OpenAI-format tool definitions for all tools."""
    return EXPLORATION_TOOLS


class LLMClient:
    """Client for LLM interactions with tool calling and cost tracking."""

    def __init__(
        self,
        model: str = "gpt-5.1",
        provider: str = "openai",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        track_cost: Optional[bool] = None,
        app_name: str = DEFAULT_APP_NAME,
        app_url: str = DEFAULT_APP_URL,
    ):
        """
        Initialize LLM client.

        Args:
            model: Model name (e.g., "gpt-5.1" for OpenAI, "openai/gpt-5.1" for OpenRouter)
            provider: Provider name ("openai" or "openrouter")
            api_key: API key (or from environment)
            base_url: Override base URL for API
            track_cost: Enable cost tracking (default: True for OpenRouter, False for OpenAI)
            app_name: App name for OpenRouter dashboard
            app_url: App URL for OpenRouter HTTP-Referer header
        """
        self.model = model
        self.provider = provider

        # Cost tracking: default True for OpenRouter, False for OpenAI
        self.track_cost = track_cost if track_cost is not None else (provider == "openrouter")

        # Configure provider
        self.config = ProviderConfig.from_provider(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            app_name=app_name,
            app_url=app_url,
        )

        # Initialize cost tracker (only meaningful for OpenRouter)
        self.cost_tracker = CostTracker(
            enabled=self.track_cost and provider == "openrouter",
        )

        # Initialize OpenAI client
        self._client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            default_headers=self.config.default_headers if self.config.default_headers else None,
        )

    def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
        step: Optional[int] = None,
        phase: Optional[str] = None,
    ) -> tuple[dict, UsageStats]:
        """
        Send a chat completion request.

        Args:
            messages: Conversation messages
            tools: Tool definitions (OpenAI format)
            tool_choice: "auto", "none", or specific tool
            step: Current step number (for logging)
            phase: Current phase (for logging)

        Returns:
            Tuple of (response_dict, usage_stats)
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

        # Enable usage tracking for OpenRouter
        if self.provider == "openrouter":
            kwargs["extra_body"] = {"usage": {"include": True}}

        log_llm_request(
            model=self.model,
            messages_count=len(messages),
            has_tools=bool(tools),
            step=step,
            phase=phase,
        )

        response = self._client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        # Extract usage stats (including cost from OpenRouter)
        cost_usd = None
        if response.usage and self.provider == "openrouter":
            # OpenRouter includes cost in response.usage.cost when extra_body.usage.include=True
            cost_usd = getattr(response.usage, "cost", None)

        usage = UsageStats(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
            generation_id=response.id,
            cost_usd=cost_usd,
        )

        # Track cost if enabled
        if self.track_cost and self.provider == "openrouter":
            self.cost_tracker.record_call(usage)
            if usage.cost_usd is not None:
                logger.info(f"[{phase or 'chat'}] Cost: ${usage.cost_usd:.6f}")

        result = {
            "content": message.content,
            "tool_calls": None,
        }

        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                }
                for tc in message.tool_calls
            ]

        log_llm_response(
            has_content=bool(message.content),
            tool_calls_count=len(message.tool_calls) if message.tool_calls else 0,
            step=step,
            phase=phase,
        )

        return result, usage

    def get_cost_summary(self) -> CostSummary:
        """
        Return cumulative cost statistics for this client.

        Returns:
            CostSummary with accumulated statistics
        """
        return self.cost_tracker.get_summary(
            provider=self.provider,
            model=self.model,
        )

    def run_tool_loop(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_handlers: dict[str, ToolFunction],
        max_steps: int = 200,
        phase: Optional[str] = None,
    ) -> tuple[str, list[dict], int]:
        """
        Run tool calling loop until completion.

        Args:
            messages: Initial messages
            tools: Tool definitions
            tool_handlers: Map of tool name to handler function
            max_steps: Maximum iterations
            phase: Current pipeline phase (for logging)

        Returns:
            Tuple of (final_response, updated_messages, steps_taken)
        """
        messages = list(messages)  # Copy

        for step in range(max_steps):
            response, _usage = self.chat(messages, tools=tools, step=step, phase=phase)

            # No tool calls - we're done
            if not response["tool_calls"]:
                logger.info(f"[{phase}] Completed after {step + 1} steps (no more tool calls)")
                return response["content"] or "", messages, step + 1

            # Add assistant message with tool calls
            assistant_msg = {"role": "assistant", "content": response["content"]}
            if response["tool_calls"]:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in response["tool_calls"]
                ]
            messages.append(assistant_msg)

            # Execute tool calls
            for tc in response["tool_calls"]:
                tool_name = tc["name"]
                tool_args = tc["arguments"]

                log_tool_call(tool_name, tool_args, step=step, phase=phase)

                # Special handling for finish_exploration
                if tool_name == "finish_exploration":
                    understanding = tool_args.get("understanding", "")
                    log_tool_result(tool_name, f"Exploration complete ({len(understanding)} chars)", step=step, phase=phase)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": "Exploration complete.",
                    })
                    logger.info(f"[{phase}] Finished after {step + 1} steps via finish_exploration")
                    return understanding, messages, step + 1

                # Execute tool
                handler = tool_handlers.get(tool_name)
                if handler:
                    try:
                        start_time = time.time()
                        result = handler(**tool_args)
                        duration_ms = (time.time() - start_time) * 1000
                        result_str = json.dumps(result, indent=2, default=str)
                        log_tool_result(tool_name, result, duration_ms=duration_ms, step=step, phase=phase)
                    except Exception as e:
                        result_str = f"Error: {str(e)}"
                        logger.error(f"[{phase}] Tool {tool_name} failed: {e}")
                else:
                    result_str = f"Unknown tool: {tool_name}"
                    logger.warning(f"[{phase}] Unknown tool called: {tool_name}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_str,
                })

        logger.warning(f"[{phase}] Hit max steps limit ({max_steps})")
        return "Max steps reached", messages, max_steps
