import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from autogen_agentchat.agents import AssistantAgent

# Works with any OpenAI API compatible LLM which is most of them 
from autogen_ext.models.openai import OpenAIChatCompletionClient
import argparse

# Add the noframework/python directory to sys.path to import common modules
noframework_path = Path(__file__).parent.parent.parent / "noframework" / "python"
sys.path.insert(0, str(noframework_path))

from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    #REACT_SYSTEM_PROMPT,
    TECH_WRITER_SYSTEM_PROMPT,
    configure_code_base_source,
    get_command_line_args,
    MAX_ITERATIONS,
    vendor_model_with_colons,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
)

from common.tools import find_all_matching_files, read_file
from common.logging import logger, configure_logging


# Async wrapper functions for AutoGen compatibility
async def find_all_matching_files_async(
    directory: str, 
    pattern: str = "*", 
    respect_gitignore: bool = True, 
    include_hidden: bool = False,
    include_subdirs: bool = True
) -> List[str]:
    """Find all the files in a given directory matching a certain regex pattern 
    optionally recursively (on by default),
    optionally include hidden files (off by default),
    respecting git's .gitignore file (on by default)
    """
    return find_all_matching_files(
        directory=directory,
        pattern=pattern,
        respect_gitignore=respect_gitignore,
        include_hidden=include_hidden,
        include_subdirs=include_subdirs,
        return_paths_as="str"
    )

async def read_file_async(file_path: str) -> Dict[str, Any]:
    """Read the contents of a specific file.
    
    Use this when you need to examine the actual content of a file.
    Provide either an absolute path or a path relative to the base directory.
    Returns the file content or an error message.
    """
    return read_file(file_path)


async def analyze_codebase(directory_path: str, prompt_file_path: str, model_name: str, base_url: str = None, repo_url: str = None, max_iters = MAX_ITERATIONS) -> tuple[str, str, str]:
    prompt = read_prompt_file(prompt_file_path)
    
    # Autogen relies 100% on OpenAI-compatible endpoints, which is most of them
    # but it does have a hard-coded list of models that limits things a bit  
    # default string sent is openai/gpt-4.1-mini which is SOTA cheap model currently
    _, model_id = model_name.split("/", 1)
    
    # Configure the model client based on vendor
    model_client = OpenAIChatCompletionClient(
        model=model_id,
    )
  
    # Create the agent with tools
    agent = AssistantAgent(
        name="tech_writer",
        model_client=model_client,
        tools=[find_all_matching_files_async, read_file_async],
        system_message=TECH_WRITER_SYSTEM_PROMPT,
        reflect_on_tool_use=True
    )
    
    task_message = f"Base directory: {directory_path}\n\n{prompt}"
    result = await agent.run(task=task_message)
    analysis_result = result.messages[-1].content
        
    repo_name = Path(directory_path).name
    return analysis_result, repo_name, repo_url or ""


def main():
    import asyncio
    
    async def async_main():
        try:
            configure_logging()
            args = get_command_line_args()
            
            repo_url, directory_path = configure_code_base_source(
                args.repo, args.directory, args.cache_dir
            )
            
            analysis_result, repo_name, _ = await analyze_codebase(
                directory_path, 
                args.prompt_file, 
                args.model, 
                args.base_url, 
                repo_url,
                getattr(args, 'max_iters', MAX_ITERATIONS)
            )
            
            output_file = save_results(
                analysis_result, args.model, repo_name, 
                args.output_dir, args.extension, args.file_name
            )
            logger.info(f"Analysis complete. Results saved to: {output_file}")
            
            create_metadata(
                output_file, args.model, repo_url, repo_name, 
                analysis_result, getattr(args, 'eval_prompt', None)
            )
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            sys.exit(1)
    
    asyncio.run(async_main())


if __name__ == "__main__":
    main()