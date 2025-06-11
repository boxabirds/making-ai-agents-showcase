from pathlib import Path
import json
import re
from openai import OpenAI
import inspect
import typing
import sys
import dspy

from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    TECH_WRITER_SYSTEM_PROMPT,
    configure_code_base_source,
    get_command_line_args,
    MAX_ITERATIONS,
)

from common.tools import TOOLS
from common.logging import logger, configure_logging

class WriteTechArticle(dspy.Signature):
    """Write a technical article based on codebase analysis."""
    prompt = dspy.InputField(desc="User's analysis prompt with base directory")
    article = dspy.OutputField(desc="Comprehensive technical article in Markdown")


class TechWriterDSPy(dspy.Module):
    def __init__(self, max_iters: int = MAX_ITERATIONS):
        super().__init__()
        
        # Create ReAct module with ONLY the 3 tools from TOOLS dict
        self.writer = dspy.ReAct(
            WriteTechArticle,
            tools=list(TOOLS.values()),  # Use the exact tools from TOOLS dict
            max_iters=max_iters
        )
        
        # Set the system prompt using the carefully structured constants
        self.writer.actor.signature.instructions = TECH_WRITER_SYSTEM_PROMPT
        
    def forward(self, prompt: str):
        """Generate technical article analyzing the codebase."""
        result = self.writer(prompt=prompt)
        return result.article

def analyse_codebase(directory_path: str, prompt_file_path: str, model_name: str, base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:
    dspy.configure(lm=dspy.LM(model_name))

    prompt = read_prompt_file(prompt_file_path)
    full_prompt = TECH_WRITER_SYSTEM_PROMPT + prompt 
    
    writer = TechWriterDSPy(max_iters=args.max_iters)

    analysis_result = writer(user_request=full_prompt)

    repo_name = Path(directory_path).name
    return analysis_result, repo_name, repo_url or ""


def main():
    try:
        configure_logging()
        args = get_command_line_args()
        repo_url, directory_path = configure_code_base_source(args.repo, args.directory, args.cache_dir)
            
        analysis_result, repo_name, _ = analyse_codebase(directory_path, args.prompt_file, args.model, args.base_url, repo_url)

        output_file = save_results(analysis_result, args.model, repo_name, args.output_dir, args.extension, args.file_name)
        logger.info(f"Analysis complete. Results saved to: {output_file}")

        create_metadata(output_file, args.model, repo_url, repo_name, analysis_result, args.eval_prompt)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()