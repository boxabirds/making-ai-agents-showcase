from typing import List, Dict, Any, Union
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
    include_subdirs: bool = True,
    return_paths_as: str = "Path"
    ) -> List[Union[Path, str]]:
    """
    Find files matching a pattern while respecting .gitignore.
    
    Args:
        directory: Directory to search in
        pattern: File pattern to match (glob format)
        respect_gitignore: Whether to respect .gitignore patterns
        include_hidden: Whether to include hidden files and directories
        include_subdirs: Whether to include files in subdirectories
        return_paths_as: Return type for paths - "Path" for Path objects, "str" for strings
        
    Returns:
        List of Path objects or strings for matching files
    """
    logger.info(f"Tool invoked: find_all_matching_files(directory='{directory}', pattern='{pattern}', respect_gitignore={respect_gitignore}, include_hidden={include_hidden}, include_subdirs={include_subdirs})")
    
    try:
        directory_path = Path(directory).resolve()
        logger.debug(f"Resolved directory path: {directory_path}")
        
        if not directory_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return []
        
        # Get gitignore spec if needed
        spec = get_gitignore_spec(str(directory_path)) if respect_gitignore else None
        if spec:
            logger.debug(f"Loaded .gitignore patterns from {directory_path}")
        else:
            logger.debug("No .gitignore patterns loaded (respect_gitignore=False or no .gitignore file)")
        
        result = []
        
        # Choose between recursive and non-recursive search
        if include_subdirs:
            logger.debug(f"Using recursive search (rglob) with pattern: {pattern}")
            paths = directory_path.rglob(pattern)
        else:
            logger.debug(f"Using non-recursive search (glob) with pattern: {pattern}")
            paths = directory_path.glob(pattern)
            
        for path in paths:
            if path.is_file():
                # Skip hidden files if not explicitly included
                # But only skip if they're in hidden directories
                if not include_hidden and path.name.startswith('.'):
                    # Check if any parent directory is hidden (excluding the file itself)
                    rel_path = path.relative_to(directory_path)
                    parent_parts = rel_path.parts[:-1]  # Exclude the filename
                    has_hidden_parent = any(part.startswith('.') for part in parent_parts)
                    
                    # Only skip if it's in a hidden directory, not just a hidden file in root
                    if has_hidden_parent:
                        logger.debug(f"Skipping hidden file in hidden directory: {path}")
                        continue
                    # Hidden files in non-hidden directories (like .gitignore) should be included
                
                # Skip if should be ignored
                if respect_gitignore and spec:
                    # Use pathlib to get relative path and convert to posix format
                    rel_path = path.relative_to(directory_path)
                    rel_path_posix = rel_path.as_posix()
                    if spec.match_file(rel_path_posix):
                        logger.debug(f"Skipping gitignored file: {rel_path_posix}")
                        continue
                result.append(path)
        
        logger.info(f"Found {len(result)} matching files")
        logger.debug(f"Matching files: {[str(p) for p in result[:10]]}{'...' if len(result) > 10 else ''}")
        
        # Return as strings if requested
        if return_paths_as == "str":
            return [str(p) for p in result]
        return result
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"Error accessing files: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error finding files: {e}")
        return []


# Tool wrapper functions for JSON compatibility
def find_all_matching_files_json(
    directory: str, 
    pattern: str = "*", 
    respect_gitignore: bool = True, 
    include_hidden: bool = False,
    include_subdirs: bool = True
) -> List[str]:
    """
    Wrapper for find_all_matching_files that returns paths as strings for JSON serialization.
    
    This is useful for frameworks that require JSON-serializable outputs (e.g., ADK, LangChain).
    """
    return find_all_matching_files(
        directory=directory,
        pattern=pattern,
        respect_gitignore=respect_gitignore,
        include_hidden=include_hidden,
        include_subdirs=include_subdirs,
        return_paths_as="str"
    )

def read_file(file_path: str) -> Dict[str, Any]:
    """Read the contents of a file."""
    logger.info(f"Tool invoked: read_file(file_path='{file_path}')")
    
    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        if is_binary(file_path):
            logger.debug(f"File detected as binary: {file_path}")
            return {"error": f"Cannot read binary file: {file_path}"}
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_size = len(content)
        logger.info(f"Successfully read file: {file_path} ({file_size} chars)")
        logger.debug(f"File has {content.count(chr(10))} lines")
        
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

# Dictionary mapping tool names to their functions
TOOLS = {
    "find_all_matching_files": find_all_matching_files,
    "read_file": read_file,
}

TOOLS_JSON = {
    "find_all_matching_files": find_all_matching_files_json,
    "read_file": read_file,
}
