"""
Logging infrastructure for tech_writer.

Provides structured logging for:
- Tool calls and results
- LLM interactions
- Pipeline phases
- Performance metrics
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Module-level logger
logger = logging.getLogger("tech_writer")

# Log levels
LOG_LEVEL_ENV = "TECH_WRITER_LOG_LEVEL"
LOG_FILE_ENV = "TECH_WRITER_LOG_FILE"

# Default log directory
DEFAULT_LOG_DIR = Path.home() / ".tech_writer" / "logs"


def configure_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure logging for tech_writer.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Default from env or INFO.
        log_file: Path to log file. Default from env or auto-generated.
        console: Whether to also log to stderr.

    Returns:
        Configured logger instance.
    """
    # Determine log level
    level_str = level or os.environ.get(LOG_LEVEL_ENV, "INFO")
    log_level = getattr(logging, level_str.upper(), logging.INFO)

    # Configure root tech_writer logger
    logger.setLevel(log_level)
    logger.handlers.clear()

    # Formatter with timestamp and context
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stderr so it doesn't mix with report output)
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    file_path = log_file or os.environ.get(LOG_FILE_ENV)
    if file_path is None:
        # Auto-generate log file path
        DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        file_path = DEFAULT_LOG_DIR / f"tech_writer_{timestamp}.log"

    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.DEBUG)  # Always capture everything to file
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logging configured: level={level_str}, file={file_path}")
    return logger


def log_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    step: Optional[int] = None,
    phase: Optional[str] = None,
) -> None:
    """
    Log a tool call.

    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments
        step: Current step number
        phase: Current pipeline phase
    """
    prefix = ""
    if phase:
        prefix += f"[{phase}] "
    if step is not None:
        prefix += f"Step {step}: "

    # Truncate large arguments for readability
    args_str = json.dumps(arguments, default=str)
    if len(args_str) > 200:
        args_str = args_str[:200] + "..."

    logger.info(f"{prefix}TOOL_CALL: {tool_name}({args_str})")


def log_tool_result(
    tool_name: str,
    result: Any,
    duration_ms: Optional[float] = None,
    step: Optional[int] = None,
    phase: Optional[str] = None,
) -> None:
    """
    Log a tool result.

    Args:
        tool_name: Name of the tool
        result: Tool result
        duration_ms: Execution time in milliseconds
        step: Current step number
        phase: Current pipeline phase
    """
    prefix = ""
    if phase:
        prefix += f"[{phase}] "
    if step is not None:
        prefix += f"Step {step}: "

    # Summarize result
    if isinstance(result, str):
        result_summary = f"{len(result)} chars"
        if len(result) < 100:
            result_summary = result
    elif isinstance(result, list):
        result_summary = f"{len(result)} items"
    elif isinstance(result, dict):
        result_summary = f"{len(result)} keys"
    else:
        result_summary = str(result)[:100]

    duration_str = f" ({duration_ms:.0f}ms)" if duration_ms else ""
    logger.info(f"{prefix}TOOL_RESULT: {tool_name} -> {result_summary}{duration_str}")


def log_llm_request(
    model: str,
    messages_count: int,
    has_tools: bool,
    step: Optional[int] = None,
    phase: Optional[str] = None,
) -> None:
    """Log an LLM API request."""
    prefix = ""
    if phase:
        prefix += f"[{phase}] "
    if step is not None:
        prefix += f"Step {step}: "

    tools_str = " with tools" if has_tools else ""
    logger.info(f"{prefix}LLM_REQUEST: {model}, {messages_count} messages{tools_str}")


def log_llm_response(
    has_content: bool,
    tool_calls_count: int,
    step: Optional[int] = None,
    phase: Optional[str] = None,
) -> None:
    """Log an LLM API response."""
    prefix = ""
    if phase:
        prefix += f"[{phase}] "
    if step is not None:
        prefix += f"Step {step}: "

    if tool_calls_count > 0:
        logger.info(f"{prefix}LLM_RESPONSE: {tool_calls_count} tool calls")
    elif has_content:
        logger.info(f"{prefix}LLM_RESPONSE: text content (no tools)")
    else:
        logger.info(f"{prefix}LLM_RESPONSE: empty")


def log_phase_start(phase: str, details: Optional[str] = None) -> None:
    """Log the start of a pipeline phase."""
    msg = f"=== PHASE START: {phase} ==="
    if details:
        msg += f" ({details})"
    logger.info(msg)


def log_phase_end(phase: str, details: Optional[str] = None) -> None:
    """Log the end of a pipeline phase."""
    msg = f"=== PHASE END: {phase} ==="
    if details:
        msg += f" ({details})"
    logger.info(msg)


def log_exploration_summary(
    files_cached: int,
    symbols_found: int,
    steps_taken: int,
    understanding_preview: str,
) -> None:
    """Log summary of exploration phase."""
    logger.info(f"EXPLORATION SUMMARY:")
    logger.info(f"  Files cached: {files_cached}")
    logger.info(f"  Symbols indexed: {symbols_found}")
    logger.info(f"  Steps taken: {steps_taken}")
    logger.info(f"  Understanding: {understanding_preview[:200]}...")
