"""Tests package."""
import os
import sys
from pathlib import Path

# Add project root to path before any imports
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

# Load .env.test if it exists (for API keys in local development)
_env_test_path = _project_root / ".env.test"
if _env_test_path.exists():
    with open(_env_test_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                # Don't override existing env vars
                if key not in os.environ:
                    os.environ[key] = value
