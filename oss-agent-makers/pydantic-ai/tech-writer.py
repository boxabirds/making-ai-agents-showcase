from pathlib import Path
import sys
from typing import Tuple
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

# Add noframework/python to path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'noframework' / 'python'))

from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    TECH_WRITER_SYSTEM_PROMPT,
    configure_code_base_source,
    get_command_line_args,
    MAX_ITERATIONS,
    vendor_model_with_colons,
)

from common.tools import find_all_matching_files, read_file
from common.logging import logger, configure_logging


class AnalysisContext(BaseModel):
    """Context dependencies for the analysis."""
    base_directory: str
    analysis_prompt: str


tech_writer = Agent(
    deps_type=AnalysisContext,
    result_type=str,
    system_prompt=TECH_WRITER_SYSTEM_PROMPT,
)

@tech_writer.tool
async def find_files(
    ctx: RunContext[AnalysisContext], 
    pattern: str = "*", 
    respect_gitignore: bool = True, 
    include_hidden: bool = False,
    include_subdirs: bool = True
) -> list[str]:
    return find_all_matching_files(
        directory=ctx.deps.base_directory,
        pattern=pattern,
        respect_gitignore=respect_gitignore,
        include_hidden=include_hidden,
        include_subdirs=include_subdirs,
        return_paths_as="str"
    )

@tech_writer.tool
async def read_file_content(ctx: RunContext[AnalysisContext], file_path: str) -> dict:
    """Read the contents of a specific file.
    
    Use this when you need to examine the actual content of a file.
    Provide either an absolute path or a path relative to the base directory.
    Returns the file content or an error message.
    """

    if not Path(file_path).is_absolute():
        file_path = str(Path(ctx.deps.base_directory) / file_path)
    return read_file(file_path)


async def analyze_codebase(
    directory_path: str, 
    prompt_file_path: str, 
    model_name: str, 
    base_url: str = None, 
    repo_url: str = None,
    max_iterations: int = MAX_ITERATIONS # not used in this framework
) -> Tuple[str, str, str]:

    prompt = read_prompt_file(prompt_file_path)
    
    context = AnalysisContext(
        base_directory=directory_path,
        analysis_prompt=prompt
    )
    
    colon_delimited_vendor_model_pair = vendor_model_with_colons(model_name)
    
    result = await tech_writer.run(
        f"Base directory: {directory_path}\n\n{prompt}",
        deps=context,
        model=colon_delimited_vendor_model_pair
    )
    
    repo_name = Path(directory_path).name
    return result.output, repo_name, repo_url or ""


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