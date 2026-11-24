import sys
import os
import traceback
from pathlib import Path

# Add paths
base_dir = Path(__file__).resolve().parent
backend_dir = (base_dir.parent / "backend").resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(base_dir.parent) not in sys.path:
    sys.path.insert(0, str(base_dir.parent))

try:
    from app.main import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    err_trace = traceback.format_exc()
    app = FastAPI()

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    def fallback(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Startup Exception in FastAPI",
                "exception": str(e),
                "traceback": err_trace,
                "sys_path": sys.path,
                "files_in_dir": [str(p) for p in base_dir.parent.glob("*")]
            }
        )
