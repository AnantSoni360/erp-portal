import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import engine, Base
from app.routers import auth, dashboard, materials, inward, transactions, contractors, verification, reports, audit, procurement, billing

# Safely ensure database tables exist without crashing on cold starts
try:
    Base.metadata.create_all(bind=engine)
except Exception as _e:
    print(f"Startup notice: Table creation skipped or existing: {_e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="MMTPL Store & Inventory Management ERP Portal Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers (Mount with /api and also root for flexible routing)
_all_routers = [
    auth.router, dashboard.router, materials.router, inward.router, 
    transactions.router, contractors.router, verification.router, 
    reports.router, audit.router, procurement.router, billing.router
]

for r in _all_routers:
    app.include_router(r, prefix=settings.API_V1_STR)
    app.include_router(r)

@app.get("/health")
@app.get("/api/health")
def health_check():
    db_ok = True
    err_msg = None
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_ok = False
        err_msg = str(e)

    return {
        "status": "healthy" if db_ok else "database_connection_error",
        "service": settings.PROJECT_NAME,
        "database_connected": db_ok,
        "database_type": settings.DATABASE_URL.split("://")[0],
        "database_host": settings.DATABASE_URL.split("@")[-1].split("/")[0] if "@" in settings.DATABASE_URL else "local_sqlite",
        "error": err_msg
    }

# Mount static frontend build if present
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
