mport sys  
import os  
import textwrap  
import instructor  
import json  
from pathlib import Path  
from typing import Optional, List, Dict, Any, Union  
from pydantic import Field  
  
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema  
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase  
from atomic_agents.lib.components.agent_memory import AgentMemory  
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig  
  
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "baremetal" / "python"))  
from common.utils import (  
    read_prompt_file,  
    save_results,  
    create_metadata,  
    ROLE_AND_TASK,  
    GENERAL_ANALYSIS_GUIDELINES,  
    INPUT_PROCESSING_GUIDELINES,  
    CODE_ANALYSIS_STRATEGIES,  
    QUALITY_REQUIREMENTS,  
    REACT_PLANNING_STRATEGY,  
    configure_code_base_source,  
    get_command_line_args,  
    CustomEncoder  
)  
from common.logging import logger, configure_logging  
from common.tools import TOOLS  
  
# Atomic Agents Schema Definitions  
class TechWriterInputSchema(BaseIOSchema):  
    """Input schema for the tech writer agent."""  
    prompt: str = Field(..., description="The analysis prompt")  
    directory: str = Field(..., description="Base directory path to analyze")  
  
class TechWriterOutputSchema(BaseIOSchema):  
    """Output schema for the tech writer agent."""  
    analysis_result: str = Field(..., description="The final analysis result")  
  
# Context Provider for dynamic codebase information  
class CodebaseContextProvider(SystemPromptContextProviderBase):  
    def __init__(self, title: str):  
        super().__init__(title=title)  
        self.base_directory = None  
        self.analysis_prompt = None  
      
    def get_info(self) -> str:  
        return f"Base directory: {self.base_directory}\n\nAnalysis prompt: {self.analysis_prompt}"  
  
# FindAllMatchingFilesTool  
class FindAllMatchingFilesInputSchema(BaseIOSchema):  
    """Input schema for finding matching files."""  
    directory: str = Field(..., description="Directory to search in")  
    pattern: str = Field(default="*", description="File pattern to match (glob format)")  
    respect_gitignore: bool = Field(default=True, description="Whether to respect .gitignore patterns")  
    include_hidden: bool = Field(default=False, description="Whether to include hidden files and directories")  
    include_subdirs: bool = Field(default=True, description="Whether to include files in subdirectories")  
  
class FindAllMatchingFilesOutputSchema(BaseIOSchema):  
    """Output schema for finding matching files."""  
    result: str = Field(..., description="JSON string containing list of matching file paths")  
  
class FindAllMatchingFilesTool(BaseTool):  
    """Tool for finding files matching a pattern while respecting .gitignore."""  
    input_schema = FindAllMatchingFilesInputSchema  
    output_schema = FindAllMatchingFilesOutputSchema  
      
    def __init__(self, config: BaseToolConfig = None):  
        super().__init__(config or BaseToolConfig(  
            title="FindAllMatchingFilesTool",  
            description="Find files matching a pattern while respecting .gitignore"  
        ))  
      
    def run(self, params: FindAllMatchingFilesInputSchema) -> FindAllMatchingFilesOutputSchema:  
        try:  
            # Call your original function from TOOLS  
            tool_func = TOOLS["find_all_matching_files"]  
            result = tool_func(  
                directory=params.directory,  
                pattern=params.pattern,  
                respect_gitignore=params.respect_gitignore,  
                include_hidden=params.include_hidden,  
                include_subdirs=params.include_subdirs,  
                return_paths_as="str"  # Always return strings for JSON compatibility  
            )  
            return FindAllMatchingFilesOutputSchema(result=json.dumps(result, cls=CustomEncoder, indent=2))  
        except Exception as e:  
            return FindAllMatchingFilesOutputSchema(result=f"Error finding files: {str(e)}")  
  
# FileReaderTool  
class FileReaderInputSchema(BaseIOSchema):  
    """Input schema for reading file contents."""  
    file_path: str = Field(..., description="Path to the file to read")  
  
class FileReaderOutputSchema(BaseIOSchema):  
    """Output schema for reading file contents."""  
    result: str = Field(..., description="JSON string containing file content or error message")  
  
class FileReaderTool(BaseTool):  
    """Tool for reading the contents of a file."""  
    input_schema = FileReaderInputSchema  
    output_schema = FileReaderOutputSchema  
      
    def __init__(self, config: BaseToolConfig = None):  
        super().__init__(config or BaseToolConfig(  
            title="FileReaderTool",  
            description="Read the contents of a file"  
        ))  
      
    def run(self, params: FileReaderInputSchema) -> FileReaderOutputSchema:  
        try:  
            # Call your original function from TOOLS  
            tool_func = TOOLS["read_file"]  
            result = tool_func(params.file_path)  
            return FileReaderOutputSchema(result=json.dumps(result, cls=CustomEncoder, indent=2))  
        except Exception as e:  
            return FileReaderOutputSchema(result=f"Error reading file: {str(e)}")  
  
def create_system_prompt_generator():  
    """Create system prompt generator using existing constants."""  
    background_lines = [  
        line.strip() for line in ROLE_AND_TASK.strip().split('\n') if line.strip()  
    ] + [  
        line.strip() for line in GENERAL_ANALYSIS_GUIDELINES.strip().split('\n')  
        if line.strip() and not line.strip().startswith('Follow these guidelines:') and line.strip() != '-'  
    ]  
      
    strategy = REACT_PLANNING_STRATEGY  
    steps = [  
        line.strip() for line in strategy.strip().split('\n')  
        if line.strip() and (line.strip().startswith(('1.', '2.', '3.', '4.', '5.')))  
    ] + [  
        line.strip() for line in CODE_ANALYSIS_STRATEGIES.strip().split('\n')  
        if line.strip() and line.strip().startswith('-')  
    ]  
      
    output_instructions = [  
        line.strip() for line in INPUT_PROCESSING_GUIDELINES.strip().split('\n')  
        if line.strip() and line.strip().startswith('-')  
    ] + [  
        line.strip() for line in QUALITY_REQUIREMENTS.strip().split('\n')  
        if line.strip()  
    ]  
      
    return SystemPromptGenerator(  
        background=background_lines,  
        steps=steps,  
        output_instructions=output_instructions  
    )  
  
class TechWriterAgent:  
    def __init__(self, vendor_model: str = "openai/gpt-4o-mini"):  
        """Initialize the TechWriter agent with atomic-agents using LiteLLM."""  
          
        # Use instructor.from_litellm - this handles all the vendor/model parsing!  
        client = instructor.from_litellm( model=vendor_model )  
          
        self.tools = [FindAllMatchingFilesTool(), FileReaderTool()]  
          
        self.codebase_context = CodebaseContextProvider("Codebase Analysis Context")  
          
        system_prompt_generator = create_system_prompt_generator()  
        system_prompt_generator.context_providers["codebase_context"] = self.codebase_context  

        model_name = vendor_model.split("/", 1)[1]
        self.agent = BaseAgent(  
            BaseAgentConfig(  
                client=client,  
                model=model_name,  
                system_prompt_generator=system_prompt_generator,  
                input_schema=TechWriterInputSchema,  
                output_schema=TechWriterOutputSchema,  
                memory=AgentMemory(),  
                model_api_parameters={"temperature": 0},  
                tools=self.tools 
            )  
        )  
      
    def run(self, prompt: str, directory: str) -> str:  
        self.codebase_context.base_directory = directory  
        self.codebase_context.analysis_prompt = prompt  
          
        input_data = TechWriterInputSchema(prompt=prompt, directory=directory)  
        result = self.agent.run(input_data)  
          
        return result.analysis_result  
  
def analyse_codebase(directory_path: str, prompt_file_path: str, vendor_model: str,  
                    base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:  
    # TODO base_url support not needed -- it's only required for ollama
    prompt = read_prompt_file(prompt_file_path)  
    agent = TechWriterAgent(vendor_model)  
    analysis_result = agent.run(prompt, directory_path)  
      
    repo_name = Path(directory_path).name  
    return analysis_result, repo_name, repo_url or ""  
  
def main():  
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
        logger.error(f"Error: {str(e)}", exc_info=True)  
        sys.exit(1)  
  
if __name__ == "__main__":  
    main()