"""
Repository handling - local paths and remote cloning.

Supports:
- Local directory paths
- GitHub/GitLab/Bitbucket URLs
- Caching of cloned repos
"""

import subprocess
from pathlib import Path
from typing import Optional


DEFAULT_CACHE_DIR = "~/.cache/github"


class CloneError(Exception):
    """Error during git clone."""
    pass


def is_remote_url(repo_arg: str) -> bool:
    """
    Check if argument is a remote URL.

    Args:
        repo_arg: Repository argument

    Returns:
        True if remote URL, False if local path
    """
    if repo_arg.startswith("https://"):
        return True
    if repo_arg.startswith("http://"):
        return True
    if repo_arg.startswith("git@"):
        return True
    if repo_arg.startswith("ssh://"):
        return True
    return False


def get_repo_name(url: str) -> str:
    """
    Extract repository name from URL.

    Args:
        url: Repository URL

    Returns:
        Repository name
    """
    # Handle various URL formats
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def clone_repo(url: str, cache_dir: Path) -> Path:
    """
    Clone a git repository.

    Args:
        url: Repository URL
        cache_dir: Directory to clone into

    Returns:
        Path to cloned repository

    Raises:
        CloneError: If clone fails
    """
    repo_name = get_repo_name(url)
    cache_path = Path(cache_dir).expanduser()
    clone_path = cache_path / repo_name

    # Reuse cached clone if exists
    if clone_path.exists():
        return clone_path

    cache_path.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(clone_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise CloneError(f"Failed to clone {url}: {result.stderr}")

    return clone_path


def resolve_repo(
    repo_arg: str,
    cache_dir: Optional[str] = None,
) -> tuple[Path, bool]:
    """
    Resolve repository argument to local path.

    Args:
        repo_arg: Local path or remote URL
        cache_dir: Directory for cloned repos (default: ~/.cache/github)

    Returns:
        (local_path, is_remote)
        is_remote=True means it was cloned from a URL
    """
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR

    if is_remote_url(repo_arg):
        clone_path = clone_repo(repo_arg, Path(cache_dir))
        return clone_path, True
    else:
        # Local path
        local_path = Path(repo_arg).expanduser().resolve()
        if not local_path.exists():
            raise FileNotFoundError(f"Repository not found: {repo_arg}")
        return local_path, False


def cleanup_repo(path: Path) -> None:
    """
    Remove a cloned repository.

    Args:
        path: Path to repository
    """
    import shutil
    if path.exists():
        shutil.rmtree(path)
