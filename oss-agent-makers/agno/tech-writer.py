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
    """Factory for creating Agno models using vendor/model format."""
    
    # Map of vendors to their model classes
    VENDOR_MAP = {
        'openai': OpenAIChat,
        'anthropic': Claude,
        'google': Gemini,
        'groq': GroqChat,
    }
    
    @classmethod
    def create(cls, model_name: str, **kwargs):
        """
        Create a model instance from vendor/model format.
        
        Args:
            model_name: Model name in vendor/model format (e.g., 'openai/gpt-4')
            **kwargs: Additional arguments for model constructor
            
        Returns:
            Configured model instance
        """
        if "/" in model_name:
            vendor, model_id = model_name.split("/", 1)
        else:
            # Fallback for models without vendor prefix
            logger.warning(f"Model '{model_name}' missing vendor prefix, assuming 'openai/{model_name}'")
            vendor = "openai"
            model_id = model_name
            
        model_class = cls.VENDOR_MAP.get(vendor)
        if not model_class:
            raise ValueError(f"Unknown model vendor: {vendor}. Supported: {list(cls.VENDOR_MAP.keys())}")
            
        return model_class(id=model_id, **kwargs)


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