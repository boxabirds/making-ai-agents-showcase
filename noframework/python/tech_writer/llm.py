"""
LLM interface for tool calling.

Provides a unified interface for LLM interactions with:
- Tool registration (OpenAI function calling format)
- Tool execution loop
- Response parsing
"""

import json
import os
import time
from typing import Any, Callable, Optional

from openai import OpenAI

from tech_writer.logging import (
    log_llm_request,
    log_llm_response,
    log_tool_call,
    log_tool_result,
    logger,
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
    """Client for LLM interactions with tool calling."""

    def __init__(
        self,
        model: str = "gpt-5.1",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize LLM client.

        Args:
            model: Model name
            api_key: API key (or from environment)
            base_url: Base URL for API
        """
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
        step: Optional[int] = None,
        phase: Optional[str] = None,
    ) -> dict:
        """
        Send a chat completion request.

        Args:
            messages: Conversation messages
            tools: Tool definitions (OpenAI format)
            tool_choice: "auto", "none", or specific tool
            step: Current step number (for logging)
            phase: Current phase (for logging)

        Returns:
            Response dict with content and tool_calls
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

        log_llm_request(
            model=self.model,
            messages_count=len(messages),
            has_tools=bool(tools),
            step=step,
            phase=phase,
        )

        response = self._client.chat.completions.create(**kwargs)
        message = response.choices[0].message

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

        return result

    def run_tool_loop(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_handlers: dict[str, ToolFunction],
        max_steps: int = 50,
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
            response = self.chat(messages, tools=tools, step=step, phase=phase)

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
