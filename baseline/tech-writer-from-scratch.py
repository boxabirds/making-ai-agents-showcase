from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json
import re
import ast
import datetime
import pathspec
from pathspec.patterns import GitWildMatchPattern
import os
import argparse
import subprocess
from binaryornot.check import is_binary
from openai import OpenAI
import math
import inspect
import typing
import logging
import textwrap
import abc  # Import the abc module for abstract base classes
import sys

# Configure logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"tech-writer-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {log_file}")

# Check for API keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


# Warn if neither API key is set
if not GEMINI_API_KEY and not OPENAI_API_KEY:
    logger.warning("Neither GEMINI_API_KEY nor OPENAI_API_KEY environment variables are set.")
    logger.warning("Please set at least one of these environment variables to use the respective API.")
    logger.warning("You can get a Gemini API key from https://aistudio.google.com")
    logger.warning("You can get an OpenAI API key from https://platform.openai.com")

# Define model providers: check, high volume and fast. 
GEMINI_MODELS = ["gemini-2.0-flash"]
OPENAI_MODELS = ["gpt-4.1-mini", "gpt-4.1-nano"]



class TechWriterAgent(abc.ABC):
    """Abstract base class for codebase analysis agents."""
    
    def __init__(self, model_name="gpt-4o-mini", base_url=None):
        """Initialise the agent with the specified model."""
        self.model_name = model_name
        self.memory = []
        self.final_answer = None
        self.system_prompt = None  # To be defined by subclasses
        
        # Determine which API to use based on the model name
        if model_name in GEMINI_MODELS:
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY environment variable is not set but a Gemini model was specified.")
            self.client = OpenAI(
                api_key=GEMINI_API_KEY,
                base_url=base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
            )
        else:
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY environment variable is not set but an OpenAI model was specified.")
            self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=base_url)
    
    def create_openai_tool_definitions(self, tools_dict):
        """
        Create tool definitions from a dictionary of Python functions.
        
        Args:
            tools_dict: Dictionary mapping tool names to Python functions
            
        Returns:
            List of tool definitions formatted for the OpenAI API
        """
        tools = []
        
        for name, func in tools_dict.items():
            # Extract function signature
            sig = inspect.signature(func)
            
            # Get docstring and parse it
            docstring = inspect.getdoc(func) or ""
            description = docstring.split("\n\n")[0] if docstring else ""
            
            # Build parameters
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param in sig.parameters.items():
                # Skip self parameter for methods
                if param_name == "self":
                    continue
                
                # Get parameter type annotation
                param_type = param.annotation
                if param_type is inspect.Parameter.empty:
                    param_type = str
                
                # Get origin and args for generic types
                origin = typing.get_origin(param_type)
                args = typing.get_args(param_type)
                
                # Convert Python types to JSON Schema types
                if param_type == str:
                    json_type = "string"
                elif param_type == int:
                    json_type = "integer"
                elif param_type == float or param_type == "number":
                    json_type = "number"
                elif param_type == bool:
                    json_type = "boolean"
                elif origin is list or param_type == list:
                    json_type = "array"
                elif origin is dict or param_type == dict:
                    json_type = "object"
                else:
                    # For complex types, default to string
                    json_type = "string"
                
                # Extract parameter description from docstring
                param_desc = ""
                if docstring:
                    # Look for parameter in docstring (format: param_name: description)
                    param_pattern = rf"{param_name}:\s*(.*?)(?:\n\s*\w+:|$)"
                    param_match = re.search(param_pattern, docstring, re.DOTALL)
                    if param_match:
                        param_desc = param_match.group(1).strip()
                
                # Add parameter to schema
                parameters["properties"][param_name] = {
                    "type": json_type,
                    "description": param_desc
                }
                
                # Mark required parameters
                if param.default is inspect.Parameter.empty:
                    parameters["required"].append(param_name)
            
            # Create tool definition
            tool_def = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            }
            
            tools.append(tool_def)
        
        return tools
    
    def initialise_memory(self, prompt, directory):
        """Initialise the agent's memory with the prompt and directory."""
        if not self.system_prompt:
            raise ValueError("System prompt must be defined by subclasses")
            
        self.memory = [{"role": "system", "content": self.system_prompt}]
        self.memory.append({"role": "user", "content": f"Base directory: {directory}\n\n{prompt}"})
        self.final_answer = None
    
    def call_llm(self):
        """
        Call the LLM with the current memory and tools.
        
        Uses the OpenAI client with appropriate base_url for all models.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.memory,
                tools=self.create_openai_tool_definitions(TOOLS),
                temperature=0
            )
            return response.choices[0].message
        except Exception as e:
            error_msg = f"Error calling API: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def check_llm_result(self, assistant_message):
        """
        Check if the LLM result is a final answer or a tool call.
        
        Args:
            assistant_message: The message from the assistant
            
        Returns:
            tuple: (result_type, result_data)
                result_type: "final_answer" or "tool_calls"
                result_data: The final answer string or list of tool calls
        """
        self.memory.append(assistant_message)
        
        if assistant_message.tool_calls:
            return "tool_calls", assistant_message.tool_calls
        else:
            return "final_answer", assistant_message.content
    
    def execute_tool(self, tool_call):
        """
        Execute a tool call and return the result.
        
        Args:
            tool_call: The tool call object from the LLM
            
        Returns:
            str: The result of the tool execution
        """
        tool_name = tool_call.function.name
        
        if tool_name not in TOOLS:
            return f"Error: Unknown tool {tool_name}"
        
        try:
            # Parse the arguments
            args = json.loads(tool_call.function.arguments)
            
            # Call the tool function
            result = TOOLS[tool_name](**args)
            
            # Convert result to JSON string
            return json.dumps(result, cls=CustomEncoder, indent=2)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in tool arguments: {str(e)}"
        except TypeError as e:
            return f"Error: Invalid argument types: {str(e)}"
        except ValueError as e:
            return f"Error: Invalid argument values: {str(e)}"
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"
    
    @abc.abstractmethod
    def run(self, prompt, directory):
        """
        Run the agent to analyse a codebase.
        
        This method must be implemented by subclasses.
        
        Args:
            prompt: The analysis prompt
            directory: The directory containing the codebase to analyse
            
        Returns:
            The analysis result
        """
        pass


class ReActAgent(TechWriterAgent):
    """Agent that uses the ReAct pattern for codebase analysis."""
    
    def __init__(self, model_name="gpt-4o-mini", base_url=None):
        REACT_SYSTEM_PROMPT = f"{ROLE_AND_TASK}\n\n{GENERAL_ANALYSIS_GUIDELINES}\n\n{INPUT_PROCESSING_GUIDELINES}\n\n{CODE_ANALYSIS_STRATEGIES}\n\n{REACT_PLANNING_STRATEGY}\n\n{QUALITY_REQUIREMENTS}"

        """Initialise the ReAct agent with the specified model."""
        super().__init__(model_name, base_url)
        self.system_prompt = REACT_SYSTEM_PROMPT
    
    def run(self, prompt, directory):
        """Run the agent to analyse a codebase using the ReAct pattern."""
        self.initialise_memory(prompt, directory)
        max_steps = 15
        
        for step in range(max_steps):
            logger.info(f"\n--- Step {step + 1} ---")
            logger.debug(f"Current memory size: {len(self.memory)} messages")
            
            # Call the LLM
            try:
                assistant_message = self.call_llm()
                
                # Check the result
                result_type, result_data = self.check_llm_result(assistant_message)
                
                if result_type == "final_answer":
                    logger.info("Received final answer from LLM")
                    self.final_answer = result_data
                    break
                elif result_type == "tool_calls":
                    logger.info(f"Processing {len(result_data)} tool calls")
                    # Execute each tool call
                    for tool_call in result_data:
                        logger.debug(f"Executing tool: {tool_call.function.name} with args: {tool_call.function.arguments}")
                        # Execute the tool
                        observation = self.execute_tool(tool_call)
                        logger.debug(f"Tool result length: {len(observation) if observation else 0} chars")
                        
                        # Add the observation to memory
                        self.memory.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": observation
                        })
            except Exception as e:
                logger.error(f"Unexpected error in step {step + 1}: {e}", exc_info=True)
                self.final_answer = f"Error running code analysis: {e}"
                break
            
            logger.info(f"Memory length: {len(self.memory)} messages")
            logger.debug(f"Current memory content size: {sum(len(str(msg)) for msg in self.memory)} chars")
        
        if self.final_answer is None:
            logger.warning(f"Failed to complete analysis within {max_steps} steps")
            self.final_answer = "Failed to complete the analysis within the step limit."
        
        return self.final_answer


def analyse_codebase(directory_path: str, prompt_file_path: str, model_name: str, agent_type: str = "react", base_url: str = None) -> str:
    """
    Analyse a codebase using the specified agent type with a prompt from an external file.
    
    Args:
        directory_path: Path to directory containing codebase OR GitHub repository URL
        prompt_file_path: Path to file containing analysis prompt
        model_name: Name of model to use for analysis
        agent_type: Type of agent (react or reflexion)
        base_url: Base URL for API (optional)
        
    Returns:
        tuple: (analysis_result, repo_name)
    """
    # Read the prompt from file
    prompt = read_prompt_file(prompt_file_path)
    
    # Initialize the appropriate agent
    if agent_type == "react":
        agent = ReActAgent(model_name, base_url)
    elif agent_type == "reflexion":
        agent = ReflexionAgent(model_name, base_url)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    # Run the analysis
    analysis_result = agent.run(prompt, directory_path)
    
    # Get repository name for output file
    repo_name = Path(directory_path).name
    
    return analysis_result, repo_name

def save_results(analysis_result: str, model_name: str, agent_type: str, repo_name: str = None) -> Path:
    """
    Save analysis results to a timestamped Markdown file in the output directory.
    
    Args:
        analysis_result: The analysis text to save
        model_name: The name of the model used for analysis
        agent_type: The type of agent used (react or reflexion)
        repo_name: The name of the repository being analysed
        
    Returns:
        Path to the saved file
    """
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Include repository name in filename if available
    if repo_name:
        output_filename = f"{timestamp}-{repo_name}-{agent_type}-{model_name}.md"
    else:
        output_filename = f"{timestamp}-{agent_type}-{model_name}.md"
        
    output_path = output_dir / output_filename
    
    # Save results to markdown file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(analysis_result)
        return output_path
    except IOError as e:
        logger.error(f"Failed to save results: {str(e)}")
        raise

def main():
    try:
        args = get_command_line_args()
        
        # Handle repo cloning if specified
        if args.repo:
            if not validate_github_url(args.repo):
                raise ValueError("Invalid GitHub repository URL format")
            try:
                directory_path = str(clone_repo(args.repo, args.cache_dir))
            except Exception as e:
                logger.error(f"Failed to clone repository: {str(e)}")
                sys.exit(1)
        else:
            directory_path = args.directory
            
        # Validate directory exists
        if not Path(directory_path).exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
            
        analysis_result, repo_name = analyse_codebase(directory_path, args.prompt_file, args.model, args.agent_type, args.base_url)
        
        # Check if the result is an error message or a step limit failure
        if isinstance(analysis_result, str) and \
           (analysis_result.startswith("Error running code analysis:") or \
            analysis_result == "Failed to complete the analysis within the step limit."):
            logger.error(analysis_result)
            sys.exit(1)
        
        # Save the results
        output_file = save_results(analysis_result, args.model, args.agent_type, repo_name)
        logger.info(f"Analysis complete. Results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()