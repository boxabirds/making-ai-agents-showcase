#!/usr/bin/env python3
"""
Tech Writer Agent using Agno (phidata)
Direct port of baseline/tech-writer.py to Agno framework
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.groq import GroqChat

# Import from common directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "baseline"))
from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    REACT_SYSTEM_PROMPT,
    configure_code_base_source,
    get_command_line_args,
    find_all_matching_files_json,
)
from common.logging import logger, configure_logging
from common.tools import read_file


class ModelFactory:
    """This is unavoidably brittle glue required for the Agno library. 
    Other solutions avoid this by delegating to LiteLLM or OpenRouter"""
    
    # Map of model prefixes to their provider classes
    PROVIDER_MAP = {
        # OpenAI models
        'gpt-': OpenAIChat,
        'o1-': OpenAIChat,
        'o3-': OpenAIChat,
        # Anthropic models
        'claude-': Claude,
        # Google models
        'gemini-': Gemini,
        'models/gemini-': Gemini,  # Full Google model paths
        # Open source models via Groq
        'llama-': GroqChat,
        'llama3-': GroqChat,
        'mixtral-': GroqChat,
        'gemma-': GroqChat,
    }
    
    @classmethod
    def create(cls, model_name: str, **kwargs):
        for prefix, model_class in cls.PROVIDER_MAP.items():
            if model_name.startswith(prefix):
                return model_class(id=model_name, **kwargs)
        
        # Default to OpenAI for unknown models
        logger.warning(f"Unknown model prefix for '{model_name}', defaulting to OpenAI")
        return OpenAIChat(id=model_name, **kwargs)


def analyse_codebase(directory_path: str, prompt_file_path: str, model_name: str, base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:
    prompt = read_prompt_file(prompt_file_path)
    model = ModelFactory.create(model_name)
    agent = Agent(
        model=model,
        instructions=REACT_SYSTEM_PROMPT,
        tools=TOOLS_JSON,
        show_tool_calls=True,
        markdown=False,  # We want plain text output for consistency
    )
    agent.model.generate_content_config = {"temperature": 0}
    full_prompt = f"Base directory: {directory_path}\n\n{prompt}"
    response = agent.run(full_prompt)
    if hasattr(response, 'content'):
        analysis_result = response.content
    else:
        analysis_result = str(response)
    
    repo_name = Path(directory_path).name
    return analysis_result, repo_name, repo_url or ""


def main():
    """Main entry point matching baseline tech-writer.py interface."""
    try:
        configure_logging()
        args = get_command_line_args()
        repo_url, directory_path = configure_code_base_source(
            args.repo, args.directory, args.cache_dir
        )
        
        analysis_result, repo_name, _ = analyse_codebase(
            directory_path, args.prompt_file, args.model, args.base_url, repo_url
        )
        
        output_file = save_results(
            analysis_result, args.model, repo_name, args.output_dir, args.extension, args.file_name
        )
        logger.info(f"Analysis complete. Results saved to: {output_file}")
        
        create_metadata(
            output_file, args.model, repo_url, repo_name, analysis_result, args.eval_prompt
        )
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()