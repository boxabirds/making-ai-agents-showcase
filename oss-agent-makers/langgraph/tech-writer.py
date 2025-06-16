from pathlib import Path
import sys
from typing import Tuple, List, Dict, Any

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage

# Add noframework/python to path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "noframework" / "python"))

from common.tools import find_all_matching_files, read_file
from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    TECH_WRITER_SYSTEM_PROMPT,
    configure_code_base_source,
    get_command_line_args,
    MAX_ITERATIONS,
    vendor_model_with_colons
)

from common.logging import logger, configure_logging

async def analyze_codebase(
    directory_path: str, 
    prompt_file_path: str, 
    model_name: str, 
    base_url: str = None, 
    repo_url: str = None,
    max_iterations: int = MAX_ITERATIONS
) -> Tuple[str, str, str]:
    prompt = read_prompt_file(prompt_file_path)
    
    def find_files(pattern: str = "*", respect_gitignore: bool = True, 
                   include_hidden: bool = False, include_subdirs: bool = True) -> List[str]:
        return find_all_matching_files(
            directory=directory_path,  
            pattern=pattern,
            respect_gitignore=respect_gitignore,
            include_hidden=include_hidden,
            include_subdirs=include_subdirs,
            return_paths_as="str"
        )
    
    def read_file_with_path_resolution(file_path: str) -> Dict[str, Any]:
        if not Path(file_path).is_absolute():
            file_path = str(Path(directory_path) / file_path)
        return read_file(file_path)
    
    agent = create_react_agent(
        model=vendor_model_with_colons(model_name),
        tools=[find_files, read_file_with_path_resolution],
    )
    
    messages = [
        SystemMessage(content=TECH_WRITER_SYSTEM_PROMPT),
        HumanMessage(content=f"Base directory: {directory_path}\n\n{prompt}")
    ]
    
    result = agent.invoke(
        {"messages": messages},
        config={"recursion_limit": max_iterations}
    )
    
    final_message = result["messages"][-1]
    analysis_result = final_message.content
    
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