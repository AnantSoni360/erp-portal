import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = (Path(__file__).resolve().parent.parent / "backend").resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.main import app
