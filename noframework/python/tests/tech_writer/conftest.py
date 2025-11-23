"""
Pytest fixtures for tech_writer tests.
"""

# Import tests package to set up path
import tests  # noqa

import tempfile
from pathlib import Path

import pytest

from tech_writer.store import CacheStore


@pytest.fixture
def store():
    """Create an in-memory cache store."""
    return CacheStore()


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_repo(temp_dir):
    """Create a sample repository structure."""
    # Create a simple Python project
    (temp_dir / "README.md").write_text("# Sample Project\n\nA test project.")
    (temp_dir / "main.py").write_text('''"""Main module."""

def main():
    """Entry point."""
    print("Hello, world!")

if __name__ == "__main__":
    main()
''')
    (temp_dir / "lib").mkdir()
    (temp_dir / "lib" / "__init__.py").write_text("")
    (temp_dir / "lib" / "utils.py").write_text('''"""Utility functions."""

import os
from pathlib import Path

class Helper:
    """Helper class."""

    def __init__(self, name):
        self.name = name

    def greet(self):
        """Return greeting."""
        return f"Hello, {self.name}!"

def format_path(path):
    """Format a path."""
    return str(Path(path).resolve())
''')

    # Create .gitignore
    (temp_dir / ".gitignore").write_text("__pycache__/\n*.pyc\n.DS_Store\n")

    return temp_dir


@pytest.fixture
def context():
    """Shared context for BDD-style tests."""
    return {}
