import sys
import os
import traceback
from pathlib import Path

# Ensure backend root is in sys.path
backend_path = Path(__file__).resolve().parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

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
                "error": "Startup Exception in backend/main.py",
                "exception": str(e),
                "traceback": err_trace,
                "sys_path": sys.path,
                "env_DATABASE_URL": os.getenv("DATABASE_URL", "NOT_SET")[:35] + "..."
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
