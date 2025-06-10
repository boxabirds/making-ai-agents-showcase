from pathlib import Path
import json
import re
from openai import OpenAI
import inspect
import typing
import sys

# Import from common/utils.py
from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    REACT_SYSTEM_PROMPT,
    CustomEncoder,
    validate_github_url,
    clone_repo,
    get_command_line_args,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    GEMINI_MODELS
)

from common.tools import TOOLS
from common.logging import logger, configure_logging
class TechWriterReActAgent:
    def __init__(self, model_name="gpt-4.1-mini", base_url=None):
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

        """Initialise the ReAct agent with the specified model."""
        self.system_prompt = REACT_SYSTEM_PROMPT
   
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
                if param_name == "self":
                    continue
                
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


def analyse_codebase(directory_path: str, prompt_file_path: str, model_name: str, base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:
    """
    Analyse a codebase using the specified agent type with a prompt from an external file.
    
    Args:
        directory_path: Path to directory containing codebase
        prompt_file_path: Path to file containing analysis prompt
        model_name: Name of model to use for analysis
        base_url: Base URL for API (optional)
        repo_url: GitHub repository URL if cloned from GitHub (optional)
        
    Returns:
        tuple: (analysis_result, repo_name, repo_url)
    """
    # Read the prompt from file
    prompt = read_prompt_file(prompt_file_path)
    
    agent = TechWriterReActAgent(model_name, base_url)
    
    # Run the analysis
    analysis_result = agent.run(prompt, directory_path)
    
    # Get repository name for output file
    repo_name = Path(directory_path).name
    
    return analysis_result, repo_name, repo_url or ""


def main():
    try:
        configure_logging()
        args = get_command_line_args()
        
        # Handle repo cloning if specified
        repo_url = ""
        if args.repo:
            if not validate_github_url(args.repo):
                raise ValueError("Invalid GitHub repository URL format")
            try:
                directory_path = str(clone_repo(args.repo, args.cache_dir))
                repo_url = args.repo
            except Exception as e:
                logger.error(f"Failed to clone repository: {str(e)}")
                sys.exit(1)
        else:
            directory_path = args.directory
            
        # Validate directory exists
        if not Path(directory_path).exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
            
        analysis_result, repo_name, _ = analyse_codebase(directory_path, args.prompt_file, args.model, args.base_url, repo_url)
        
        # Check if the result is an error message or a step limit failure
        if isinstance(analysis_result, str) and \
           (analysis_result.startswith("Error running code analysis:") or \
            analysis_result == "Failed to complete the analysis within the step limit."):
            logger.error(analysis_result)
            sys.exit(1)
        
        # Save the results
        output_file = save_results(analysis_result, args.model, repo_name, args.output_dir, args.extension)
        logger.info(f"Analysis complete. Results saved to: {output_file}")
        
        # Always create metadata (with optional evaluation)
        create_metadata(output_file, args.model, repo_url, repo_name, analysis_result, args.eval_prompt)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()