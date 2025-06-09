
from pathlib import Path
import pathspec
from pathspec.patterns import GitWildMatchPattern
import logging
import textwrap
import ast
import math
import json
import re
import subprocess
import argparse
import os
from typing import List, Dict, Any
from binaryornot.check import is_binary

# Configure logging
logger = logging.getLogger(__name__)

# Check for API keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Define model providers
GEMINI_MODELS = ["gemini-2.0-flash"]
OPENAI_MODELS = ["gpt-4.1-mini", "gpt-4.1-nano"]

def save_results(analysis_result: str, model_name: str,repo_name: str = None) -> Path:
    """
    Save analysis results to a timestamped Markdown file in the output directory.
    
    Args:
        analysis_result: The analysis text to save
        model_name: The name of the model used for analysis
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
        output_filename = f"{timestamp}-{repo_name}-{model_name}.md"
    else:
        output_filename = f"{timestamp}-{model_name}.md"
        
    output_path = output_dir / output_filename
    
    # Save results to markdown file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(analysis_result)
        return output_path
    except IOError as e:
        logger.error(f"Failed to save results: {str(e)}")
        raise

def get_gitignore_spec(directory: str) -> pathspec.PathSpec:
    """
    Get a PathSpec object from .gitignore in the specified directory.
    
    Args:
        directory: The directory containing .gitignore
        
    Returns:
        A PathSpec object for matching against .gitignore patterns
    """
    ignore_patterns = []
    
    # Try to read .gitignore file
    gitignore_path = Path(directory) / ".gitignore"
    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        ignore_patterns.append(line)
                        
            logger.info(f"Added {len(ignore_patterns)} patterns from .gitignore")
        except (IOError, UnicodeDecodeError) as e:
            logger.error(f"Error reading .gitignore: {e}")
    
    # Create pathspec matcher
    return pathspec.PathSpec.from_lines(
        GitWildMatchPattern, ignore_patterns
    )

def read_prompt_file(file_path: str) -> str:
    """Read a prompt from an external file."""
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except UnicodeDecodeError:
        try:
            with open(path, 'r', encoding='latin-1') as f:
                return f.read().strip()
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"Error reading prompt file with latin-1 encoding: {str(e)}")
    except (IOError, OSError) as e:
        raise IOError(f"Error reading prompt file: {str(e)}")

# System prompt components for the tech writer agent
ROLE_AND_TASK = textwrap.dedent("""
    You are an expert tech writer that helps teams understand codebases with accurate and concise supporting analysis and documentation. 
    Your task is to analyse the local filesystem to understand the structure and functionality of a codebase.
""")

GENERAL_ANALYSIS_GUIDELINES = textwrap.dedent("""
    Follow these guidelines:
    - Use the available tools to explore the filesystem, read files, and gather information.
    - Make no assumptions about file types or formats - analyse each file based on its content and extension.
    - Focus on providing a comprehensive, accurate, and well-structured analysis.
    - Include code snippets and examples where relevant.
    - Organize your response with clear headings and sections.
    - Cite specific files and line numbers to support your observations.
""")

INPUT_PROCESSING_GUIDELINES = textwrap.dedent("""
    Important guidelines:
    - The user's analysis prompt will be provided in the initial message, prefixed with the base directory of the codebase (e.g., "Base directory: /path/to/codebase").
    - Analyse the codebase based on the instructions in the prompt, using the base directory as the root for all relative paths.
    - Make no assumptions about file types or formats - analyse each file based on its content and extension.
    - Adapt your analysis approach based on the codebase and the prompt's requirements.
    - Be thorough but focus on the most important aspects as specified in the prompt.
    - Provide clear, structured summaries of your findings in your final response.
    - Handle errors gracefully and report them clearly if they occur but don't let them halt the rest of the analysis.
""")

CODE_ANALYSIS_STRATEGIES = textwrap.dedent("""
    When analysing code:
    - Start by exploring the directory structure to understand the project organisation.
    - Identify key files like README, configuration files, or main entry points.
    - Ignore temporary files and directories like node_modules, .git, etc.
    - Analyse relationships between components (e.g., imports, function calls).
    - Look for patterns in the code organisation (e.g., line counts, TODOs).
    - Summarise your findings to help someone understand the codebase quickly, tailored to the prompt.
""")

REACT_PLANNING_STRATEGY = textwrap.dedent("""
    You should follow the ReAct pattern:
    1. Thought: Reason about what you need to do next
    2. Action: Use one of the available tools
    3. Observation: Review the results of the tool
    4. Repeat until you have enough information to provide a final answer
""")

REFLEXION_PLANNING_STRATEGY = textwrap.dedent("""
    You should follow the Reflexion pattern (an extension of ReAct):
    1. Thought: Reason about what you need to do next
    2. Action: Use one of the available tools
    3. Observation: Review the results of the tool
    4. Reflection: Analyze your approach, identify any mistakes or inefficiencies, and consider how to improve
    5. Repeat until you have enough information to provide a final answer
""")

QUALITY_REQUIREMENTS = textwrap.dedent("""
    When you've completed your analysis, provide a final answer in the form of a comprehensive Markdown document 
    that provides a mutually exclusive and collectively exhaustive (MECE) analysis of the codebase using the user prompt.

    Your analysis should be thorough, accurate, and helpful for someone trying to understand this codebase.
""")

# Combine components to form system prompts

# Tool functions
def find_all_matching_files(
    directory: str, 
    pattern: str = "*", 
    respect_gitignore: bool = True, 
    include_hidden: bool = False,
    include_subdirs: bool = True
    ) -> List[Path]:
    """
    Find files matching a pattern while respecting .gitignore.
    
    Args:
        directory: Directory to search in
        pattern: File pattern to match (glob format)
        respect_gitignore: Whether to respect .gitignore patterns
        include_hidden: Whether to include hidden files and directories
        include_subdirs: Whether to include files in subdirectories
        
    Returns:
        List of Path objects for matching files
    """
    try:
        directory_path = Path(directory).resolve()
        if not directory_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return []
        
        # Get gitignore spec if needed
        spec = get_gitignore_spec(str(directory_path)) if respect_gitignore else None
        
        result = []
        
        # Choose between recursive and non-recursive search
        if include_subdirs:
            paths = directory_path.rglob(pattern)
        else:
            paths = directory_path.glob(pattern)
            
        for path in paths:
            if path.is_file():
                # Skip hidden files if not explicitly included
                if not include_hidden and any(part.startswith('.') for part in path.parts):
                    continue
                
                # Skip if should be ignored
                if respect_gitignore and spec:
                    # Use pathlib to get relative path and convert to posix format
                    rel_path = path.relative_to(directory_path)
                    rel_path_posix = rel_path.as_posix()
                    if spec.match_file(rel_path_posix):
                        continue
                result.append(path)
        
        return result
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"Error accessing files: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error finding files: {e}")
        return []

def read_file(file_path: str) -> Dict[str, Any]:
    """Read the contents of a file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        if is_binary(file_path):
            return {"error": f"Cannot read binary file: {file_path}"}
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "file": file_path,
            "content": content
        }
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except UnicodeDecodeError:
        return {"error": f"Cannot decode file as UTF-8: {file_path}"}
    except PermissionError:
        return {"error": f"Permission denied when reading file: {file_path}"}
    except IOError as e:
        return {"error": f"IO error reading file: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error reading file: {str(e)}"}

def calculate(expression: str) -> Dict[str, Any]:
    """
    Evaluate a mathematical expression and return the result.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2 * 3")
        
    Returns:
        Dictionary containing the expression and its result
    """
    try:
        # Create a safe environment for evaluating expressions
        # This uses Python's ast.literal_eval for safety instead of eval()
        def safe_eval(expr):
            # Replace common mathematical functions with their math module equivalents
            expr = expr.replace("^", "**")  # Support for exponentiation
            
            # Parse the expression into an AST
            parsed_expr = ast.parse(expr, mode='eval')
            
            # Check that the expression only contains safe operations
            for node in ast.walk(parsed_expr):
                # Allow names that are defined in the math module
                if isinstance(node, ast.Name) and node.id not in math.__dict__:
                    if node.id not in ['True', 'False', 'None']:
                        raise ValueError(f"Invalid name in expression: {node.id}")
                
                # Only allow safe operations
                elif isinstance(node, ast.Call):
                    if not (isinstance(node.func, ast.Name) and node.func.id in math.__dict__):
                        raise ValueError(f"Invalid function call in expression")
            
            # Evaluate the expression with the math module available
            return eval(compile(parsed_expr, '<string>', 'eval'), {"__builtins__": {}}, math.__dict__)
        
        # Evaluate the expression
        result = safe_eval(expression)
        
        return {
            "expression": expression,
            "result": result
        }
    except SyntaxError as e:
        return {
            "error": f"Syntax error in expression: {str(e)}",
            "expression": expression
        }
    except ValueError as e:
        return {
            "error": f"Value error in expression: {str(e)}",
            "expression": expression
        }
    except TypeError as e:
        return {
            "error": f"Type error in expression: {str(e)}",
            "expression": expression
        }
    except Exception as e:
        return {
            "error": f"Unexpected error evaluating expression: {str(e)}",
            "expression": expression
        }

# Dictionary mapping tool names to their functions
TOOLS = {
    "find_all_matching_files": find_all_matching_files,
    "read_file": read_file,
    "calculate": calculate
}


def configure_logging():
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

    # Warn if neither API key is set
    if not GEMINI_API_KEY and not OPENAI_API_KEY:
        logger.warning("Neither GEMINI_API_KEY nor OPENAI_API_KEY environment variables are set.")
        logger.warning("Please set at least one of these environment variables to use the respective API.")
        logger.warning("You can get a Gemini API key from https://aistudio.google.com")
        logger.warning("You can get an OpenAI API key from https://platform.openai.com")


class CustomEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles Path objects from pathlib.
    
    This encoder is necessary for serializing results from tool functions
    that return Path objects, which are not JSON-serializable by default.
    Used primarily in the execute_tool method when converting tool results
    to JSON strings for the LLM.
    """
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)





def validate_github_url(url: str) -> bool:
    """Validate GitHub URL or owner/repo format."""
    # Standard GitHub URL
    url_pattern = r'^https:\/\/github\.com\/[a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+(\.git)?(\/)?$'
    # owner/repo format
    repo_pattern = r'^[a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+$'
    return re.match(url_pattern, url) is not None or re.match(repo_pattern, url) is not None


def get_repo_name_from_url(url: str) -> str:
    """Extract owner/repo from GitHub URL or return directly if already in owner/repo format."""
    if '/' in url and not url.startswith('http'):
        return url  # Already in owner/repo format
    url = url.rstrip('/').replace('.git', '')
    return '/'.join(url.split('/')[-2:])


def clone_repo(repo_url: str, cache_dir: str) -> Path:
    """
    Clone repo to cache if not exists, return local path.
    
    Args:
        repo_url: GitHub repository URL
        cache_dir: Directory to cache cloned repositories
        
    Returns:
        Path to cloned repository
    """
    repo_name = get_repo_name_from_url(repo_url)
    repo_path = Path(cache_dir) / repo_name
    if not repo_path.exists():
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(['git', 'clone', '--depth', '1', repo_url, str(repo_path)], 
                          check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e.stderr}")
            raise ValueError(f"Failed to clone repository: {repo_url}") from e
    return repo_path

def get_command_line_args():
    """Get command line arguments."""
    parser = argparse.ArgumentParser(description="Analyse a codebase using an LLM agent.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("directory", nargs='?', help="Directory containing the codebase to analyse")
    group.add_argument("--repo", help="GitHub repository URL to clone (e.g. https://github.com/owner/repo)")
    parser.add_argument("prompt_file", help="Path to a file containing the analysis prompt")
    
    # Add cache directory argument
    parser.add_argument("--cache-dir", default="output/cache",
                      help="Directory to cache cloned repositories (default: output/cache)")
    
    # Define available models based on which API keys are set
    available_models = []
    if OPENAI_API_KEY:
        available_models.extend(OPENAI_MODELS)
    if GEMINI_API_KEY:
        available_models.extend(GEMINI_MODELS)
    
    parser.add_argument("--model", choices=available_models, default=available_models[0] if available_models else None,
                      help="Model to use for analysis")
    parser.add_argument("--base-url", default=None,
                      help="Base URL for the API (automatically set based on model if not provided)")
    parser.add_argument("--agent-type", choices=["react", "reflexion"], default="react",
                      help="Type of agent to use for analysis (react or reflexion)")
    
    args = parser.parse_args()
    
    # Validate that we have a model available
    if not available_models:
        parser.error("No API keys set. Please set OPENAI_API_KEY or GEMINI_API_KEY environment variables.")
    
    return args
