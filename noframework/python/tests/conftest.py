import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is on sys.path for imports during pytest collection
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env.test for test credentials (e.g., OPENAI_API_KEY)
env_test = ROOT / ".env.test"
if env_test.exists():
    load_dotenv(env_test)
