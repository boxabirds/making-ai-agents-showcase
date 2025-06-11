#!/usr/bin/env python3
"""
Tech Writer Agent using DSPy
Direct port of baremetal/python/tech-writer.py to use DSPy framework
"""

import sys
from pathlib import Path
import json
import dspy
from typing import Dict, Any, Optional, List

# Add baremetal/python to path to import common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "baremetal" / "python"))

# Import from common modules - reuse everything possible
from common.utils import (
    read_prompt_file,
    save_results,
    create_metadata,
    configure_code_base_source,
    get_command_line_args,
    REACT_SYSTEM_PROMPT,
)
from common.tools import TOOLS, TOOLS_JSON
from common.logging import logger, configure_logging


# Define signatures for DSPy
class TechWriterSignature(dspy.Signature):
    """Analyze a codebase and generate technical documentation."""
    
    # Input fields
    prompt: str = dspy.InputField(desc="Instructions for what to analyze and document")
    base_directory: str = dspy.InputField(desc="Base directory path of the codebase to analyze")
    tools_available: str = dspy.InputField(desc="JSON description of available tools")
    
    # Output field
    analysis: str = dspy.OutputField(desc="Complete technical documentation analysis")


class ToolCallSignature(dspy.Signature):
    """Decide which tool to call and with what arguments."""
    
    # Input fields
    task: str = dspy.InputField(desc="Current task to accomplish")
    tools_available: str = dspy.InputField(desc="JSON description of available tools")
    previous_observations: str = dspy.InputField(desc="Previous tool outputs and observations")
    
    # Output fields
    reasoning: str = dspy.OutputField(desc="Reasoning about which tool to use and why")
    tool_name: str = dspy.OutputField(desc="Name of the tool to call (or 'none' if task is complete)")
    tool_args: str = dspy.OutputField(desc="JSON string of arguments for the tool (or empty if no tool)")
    

class FinalAnswerSignature(dspy.Signature):
    """Generate the final documentation based on all observations."""
    
    # Input fields
    original_prompt: str = dspy.InputField(desc="Original analysis prompt")
    all_observations: str = dspy.InputField(desc="All tool outputs and observations gathered")
    
    # Output field
    final_documentation: str = dspy.OutputField(desc="Final technical documentation")


class DSPyTechWriter(dspy.Module):
    """DSPy implementation of the Tech Writer agent."""
    
    def __init__(self, model_name: str = "openai/gpt-4o-mini"):
        super().__init__()
        
        # Parse model name
        self.model_name = model_name
        
        m = dspy.LM(model_name)
            
        dspy.configure(lm=lm)
        
        # Initialize DSPy modules
        self.tool_selector = dspy.ChainOfThought(ToolCallSignature)
        self.final_answer_generator = dspy.ChainOfThought(FinalAnswerSignature)
        
        # Store tools reference
        self.tools = TOOLS_JSON  # Use TOOLS_JSON which has the JSON-compatible wrappers
        
        # Create tool descriptions for DSPy
        tool_descriptions = {
            "find_all_matching_files": {
                "name": "find_all_matching_files",
                "description": "Find files matching a pattern while respecting .gitignore",
                "parameters": {
                    "directory": "Directory to search in (required)",
                    "pattern": "File pattern to match in glob format (default: '*')",
                    "respect_gitignore": "Whether to respect .gitignore patterns (default: true)",
                    "include_hidden": "Whether to include hidden files (default: false)",
                    "include_subdirs": "Whether to include subdirectories (default: true)"
                }
            },
            "read_file": {
                "name": "read_file",
                "description": "Read the contents of a file",
                "parameters": {
                    "file_path": "Path to the file to read (required)"
                }
            }
        }
        self.tools_json_str = json.dumps(tool_descriptions, indent=2)
        
    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Execute a tool with given arguments."""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found"
            
        try:
            logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
            result = self.tools[tool_name](**tool_args)
            
            # Convert result to string if needed
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            return str(result)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Error executing tool: {str(e)}"
    
    def forward(self, prompt: str, base_directory: str, max_steps: int = 15) -> str:
        """Run the tech writer agent with DSPy's ReAct-style approach."""
        
        logger.info(f"Starting DSPy tech writer analysis with model: {self.model_name}")
        
        # Initialize observations list
        observations = []
        
        # Add initial context
        initial_context = f"Base directory for analysis: {base_directory}"
        observations.append(initial_context)
        
        # ReAct loop
        for step in range(max_steps):
            logger.info(f"Step {step + 1}/{max_steps}")
            
            # Prepare previous observations
            previous_obs = "\n".join(observations) if observations else "No previous observations"
            
            # Decide on tool to use
            tool_decision = self.tool_selector(
                task=prompt,
                tools_available=self.tools_json_str,
                previous_observations=previous_obs
            )
            
            logger.debug(f"Tool decision reasoning: {tool_decision.reasoning}")
            logger.info(f"Selected tool: {tool_decision.tool_name}")
            
            # Check if we're done
            if tool_decision.tool_name.lower() == "none" or not tool_decision.tool_name:
                logger.info("Agent decided no more tools needed")
                break
                
            # Parse and execute tool
            try:
                # Parse tool arguments
                if tool_decision.tool_args:
                    tool_args = json.loads(tool_decision.tool_args)
                else:
                    tool_args = {}
                    
                # Map base_path to directory for find_all_matching_files
                if tool_decision.tool_name == "find_all_matching_files" and "directory" not in tool_args:
                    tool_args["directory"] = base_directory
                    
                # Execute tool
                result = self.execute_tool(tool_decision.tool_name, tool_args)
                
                # Add observation
                observation = f"Tool: {tool_decision.tool_name}\nArgs: {json.dumps(tool_args)}\nResult: {result}"
                observations.append(observation)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tool arguments: {e}")
                observations.append(f"Error: Failed to parse tool arguments for {tool_decision.tool_name}")
            except Exception as e:
                logger.error(f"Error in tool execution: {e}")
                observations.append(f"Error executing {tool_decision.tool_name}: {str(e)}")
        
        # Generate final answer
        logger.info("Generating final documentation")
        all_observations = "\n\n".join(observations)
        
        final_result = self.final_answer_generator(
            original_prompt=prompt,
            all_observations=all_observations
        )
        
        return final_result.final_documentation


def analyse_codebase(directory_path: str, prompt_file_path: str, model_name: str, base_url: str = None, repo_url: str = None) -> tuple[str, str, str]:
    """
    Analyse a codebase using DSPy tech writer agent.
    
    Args:
        directory_path: Path to directory containing codebase
        prompt_file_path: Path to file containing analysis prompt
        model_name: Name of model to use for analysis
        base_url: Base URL for API (not used in DSPy)
        repo_url: GitHub repository URL if cloned from GitHub (optional)
        
    Returns:
        tuple: (analysis_result, repo_name, repo_url)
    """
    prompt = read_prompt_file(prompt_file_path)
    
    # Create DSPy agent
    agent = DSPyTechWriter(model_name)
    
    # Run analysis
    analysis_result = agent(prompt=prompt, base_directory=directory_path)
    
    # Get repo name
    repo_name = Path(directory_path).name
    
    return analysis_result, repo_name, repo_url or ""


def main():
    """Main entry point matching baremetal tech-writer.py interface."""
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