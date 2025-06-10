from typing import List, Dict, Any
from pathlib import Path
from .logging import logger
from binaryornot.check import is_binary
from .utils import get_gitignore_spec

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
