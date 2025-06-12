import textwrap  
import instructor  
import openai  
from pathlib import Path  
from typing import Optional  
from pydantic import Field  
  
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema  
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase  
from atomic_agents.lib.components.agent_memory import AgentMemory  

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
    get_command_line_args
)
from common.logging import logger, configure_logging
from common.tools import TOOLS_JSON
  
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
        if not self.base_directory or not self.analysis_prompt:  
            return "No codebase context available."  
          
        return f"Base directory: {self.base_directory}\n\nAnalysis prompt: {self.analysis_prompt}"  
  

def create_system_prompt_generator():    
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
    def __init__(self, model_name: str = "openai/gpt-4o-mini"):  

        _, model_id = model_name.split("/", 1)            
        
        self.codebase_context = CodebaseContextProvider("Codebase Analysis Context")  
          
        system_prompt_generator = create_system_prompt_generator()  
        system_prompt_generator.context_providers["codebase_context"] = self.codebase_context  
          
        self.agent = BaseAgent(  
            BaseAgentConfig(  
                model=self.model_id,  
                system_prompt_generator=system_prompt_generator,  
                input_schema=TechWriterInputSchema,  
                output_schema=TechWriterOutputSchema,  
                memory=AgentMemory(),  
                model_api_parameters={"temperature": 0}  
            )  
        )  
      
    def run(self, prompt: str, directory: str) -> str:  
        """Run the agent to analyze a codebase."""  
        # Update context provider with current analysis info  
        self.codebase_context.base_directory = directory  
        self.codebase_context.analysis_prompt = prompt  
          
        input_data = TechWriterInputSchema(prompt=prompt, directory=directory)  
        result = self.agent.run(input_data)  
          
        return result.analysis_result  
  

def analyse_codebase(directory_path: str, prompt_file_path: str, model_name: str,   
                    base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:  
    prompt = read_prompt_file(prompt_file_path)      
    agent = TechWriterAgent(model_name)  
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