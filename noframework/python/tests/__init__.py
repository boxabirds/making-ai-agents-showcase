"""Tests package."""
import sys
from pathlib import Path

# Add project root to path before any imports
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))
