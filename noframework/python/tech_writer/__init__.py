"""
Tech Writer v2: Agentic documentation generator.

This module provides an LLM-powered agent that explores codebases
and generates technical documentation with citations.
"""

from tech_writer.store import CacheStore
from tech_writer.orchestrator import run_pipeline

__version__ = "2.0.0"
__all__ = ["CacheStore", "run_pipeline"]
