import sys
from pathlib import Path

# Add backend directory to sys.path
_current_dir = Path(__file__).resolve().parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from app.main import app as _app

# Top-level handler definition for Vercel Python runtime
app = _app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
