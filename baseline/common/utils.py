
import datetime
from pathlib import Path
import pathspec
from pathspec.patterns import GitWildMatchPattern
import textwrap
import json
import re
import subprocess
import argparse
import os
from openai import OpenAI
from .logging import logger


# Check for API keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


# Warn if neither API key is set
if not GEMINI_API_KEY and not OPENAI_API_KEY:
    logger.warning("Neither GEMINI_API_KEY nor OPENAI_API_KEY environment variables are set.")
    logger.warning("Please set at least one of these environment variables to use the respective API.")
    logger.warning("You can get a Gemini API key from https://aistudio.google.com")
    logger.warning("You can get an OpenAI API key from https://platform.openai.com")


# Define model providers
GEMINI_MODELS = ["gemini-2.0-flash"]
OPENAI_MODELS = ["gpt-4.1-mini", "gpt-4.1-nano"]

def save_results(analysis_result: str, model_name: str, repo_name: str = None, output_dir: str = None, extension: str = None) -> Path:
    """
    Save analysis results to a timestamped file in the output directory.
    
    Args:
        analysis_result: The analysis text to save
        model_name: The name of the model used for analysis
        repo_name: The name of the repository being analysed
        output_dir: The directory to save results to (default: "output")
        extension: The file extension to use (default: ".md")
        
    Returns:
        Path to the saved file
    """
    # Use default values if not provided
    if output_dir is None:
        output_dir = "output"
    if extension is None:
        extension = ".md"
    
    # Ensure extension starts with a dot
    if extension and not extension.startswith('.'):
        extension = '.' + extension
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Include repository name in filename if available
    if repo_name:
        output_filename = f"{timestamp}-{repo_name}-{model_name}{extension}"
    else:
        output_filename = f"{timestamp}-{model_name}{extension}"
        
    output_file = output_path / output_filename
    
    # Save results to file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(analysis_result)
        return output_file
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
REACT_SYSTEM_PROMPT = f"{ROLE_AND_TASK}\n\n{GENERAL_ANALYSIS_GUIDELINES}\n\n{INPUT_PROCESSING_GUIDELINES}\n\n{CODE_ANALYSIS_STRATEGIES}\n\n{REACT_PLANNING_STRATEGY}\n\n{QUALITY_REQUIREMENTS}"




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
    
    # Add output directory and extension arguments
    parser.add_argument("--output-dir", default=None,
                      help="Directory to save results to (default: output)")
    parser.add_argument("--extension", default=None,
                      help="File extension for output files (default: .md)")
    
    # Add eval prompt argument
    parser.add_argument("--eval-prompt", default=None,
                      help="Path to file containing prompt to evaluate the tech writer results")
    
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
    
    args = parser.parse_args()
    
    # Validate that we have a model available
    if not available_models:
        parser.error("No API keys set. Please set OPENAI_API_KEY or GEMINI_API_KEY environment variables.")
    
    return args


def create_metadata(output_file: Path, model_name: str, repo_url: str, repo_name: str, tech_writer_result: str, eval_prompt_file: str = None) -> None:
    """
    Create a metadata JSON file for the tech writer output.
    
    Args:
        output_file: Path to the original output file
        model_name: Model used for analysis
        repo_url: GitHub repository URL (empty string if local)
        repo_name: Repository name
        tech_writer_result: The output from the tech writer
        eval_prompt_file: Path to evaluation prompt file (optional)
    """
    try:
        metadata = {
            "model": model_name,
            "github_url": repo_url,
            "repo_name": repo_name,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Run evaluation if prompt provided
        if eval_prompt_file:
            try:
                # Read the evaluation prompt
                eval_prompt = read_prompt_file(eval_prompt_file)
                
                # Prepare the full prompt with the tech writer result
                full_prompt = f"{eval_prompt}\n\n{tech_writer_result}"
                
                # Initialize client based on model
                if model_name in GEMINI_MODELS:
                    if not GEMINI_API_KEY:
                        raise ValueError("GEMINI_API_KEY environment variable is not set")
                    client = OpenAI(
                        api_key=GEMINI_API_KEY,
                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                    )
                else:
                    if not OPENAI_API_KEY:
                        raise ValueError("OPENAI_API_KEY environment variable is not set")
                    client = OpenAI(api_key=OPENAI_API_KEY)
                
                # Call the API for evaluation
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0
                )
                
                eval_result = response.choices[0].message.content
                metadata["eval_output"] = eval_result
                
            except Exception as e:
                logger.error(f"Error running evaluation: {str(e)}")
                metadata["eval_error"] = str(e)
        
        # Create metadata filename
        # If output file is "file.sh", metadata file will be "file.metadata.json"
        metadata_file = output_file.parent / f"{output_file.stem}.metadata.json"
        
        # Save the metadata
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to: {metadata_file}")
        
    except Exception as e:
        logger.error(f"Error creating metadata: {str(e)}")
        raise
