#!/usr/bin/env python3
"""
Tech Writer Agent using DSPy's built-in ReAct module.

This implementation uses DSPy's native ReAct agent for tool-based reasoning.
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add baremetal/python to path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "baremetal" / "python"))

import dspy
from common.utils import (
    get_command_line_args,
    read_prompt_file,
    save_results,
    create_metadata,
    configure_code_base_source,
    logger,
    CustomEncoder,
)
from common.tools import TOOLS

# DSPy uses docstrings as functional units -- it uses it as the main prompt. 
# This approach can be very problematic because it prevents you from easily
# being able to use variables for your prompt, which is clearly nonsense.
# You'd have to do this hack below to modify the __doc__ variable:
# class TechWriterSignature(dspy.Signature):

#     TechWriterSignature.__doc__ = TECH_WRITER_SYSTEM_PROMPT
#     😱
# So I've inlined the text prompts. 


class TechWriterSignature(dspy.Signature):
    """
    You are an expert tech writer that helps teams understand codebases with accurate and concise supporting analysis and documentation. 
    Your task is to analyse the local filesystem to understand the structure and functionality of a codebase.

     Follow these guidelines:
    - Use the available tools to explore the filesystem, read files, and gather information.
    - Make no assumptions about file types or formats - analyse each file based on its content and extension.
    - Focus on providing a comprehensive, accurate, and well-structured analysis.
    - Include code snippets and examples where relevant.
    - Organize your response with clear headings and sections.
    - Cite specific files and line numbers to support your observations.

    Important guidelines:
    - The user's analysis prompt will be provided in the initial message, prefixed with the base directory of the codebase (e.g., "Base directory: /path/to/codebase").
    - Analyse the codebase based on the instructions in the prompt, using the base directory as the root for all relative paths.
    - Make no assumptions about file types or formats - analyse each file based on its content and extension.
    - Adapt your analysis approach based on the codebase and the prompt's requirements.
    - Be thorough but focus on the most important aspects as specified in the prompt.
    - Provide clear, structured summaries of your findings in your final response.
    - Handle errors gracefully and report them clearly if they occur but don't let them halt the rest of the analysis.

    When analysing code:
    - Start by exploring the directory structure to understand the project organisation.
    - Identify key files like README, configuration files, or main entry points.
    - Ignore temporary files and directories like node_modules, .git, etc.
    - Analyse relationships between components (e.g., imports, function calls).
    - Look for patterns in the code organisation (e.g., line counts, TODOs).
    - Summarise your findings to help someone understand the codebase quickly, tailored to the prompt.

    When you've completed your analysis, provide a final answer in the form of a comprehensive Markdown document 
    that provides a mutually exclusive and collectively exhaustive (MECE) analysis of the codebase using the user prompt.

    Your analysis should be thorough, accurate, and helpful for someone trying to understand this codebase.

    """

    # TODO the prompt above is a copy of the master prompt in TECH_WRITER_SYSTEM_PROMPT so if that changes, this has to be updated manually
    
    prompt: str = dspy.InputField(desc="The analysis prompt and base directory")
    analysis: str = dspy.OutputField(desc="Comprehensive markdown analysis of the codebase")

def analyse_codebase(directory_path: str, prompt_file_path: str, model_name: str, base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:
    dspy.configure(lm=dspy.LM(model=model_name))
    
    prompt_content = read_prompt_file(prompt_file_path)
    full_prompt = f"Base directory for analysis: {directory_path}\n\n{prompt_content}"
    
    logger.info(f"Starting DSPy ReAct tech writer with model: {model_name}")
    logger.info(f"Analyzing directory: {directory_path}")
    
    react_agent = dspy.ReAct(TechWriterSignature, tools=list(TOOLS.values()), max_iters=20)
    result = react_agent(prompt=full_prompt)
    analysis = result.analysis
    
    repo_name = Path(directory_path).name
    return analysis, repo_name, repo_url or ""


def main():
    try:
        from common.logging import configure_logging
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