import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

def _create_robust_engine():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    try:
        eng = create_engine(
            db_url,
            connect_args=connect_args,
            pool_pre_ping=True
        )
        # Test connection
        if not db_url.startswith("sqlite"):
            with eng.connect() as conn:
                pass
        return eng
    except Exception as e:
        print(f"Warning: Primary database connection failed: {e}. Falling back to SQLite.", flush=True)
        # Fallback to local SQLite so app never crashes
        base_dir = Path(__file__).resolve().parent.parent
        tmp_db = Path("/tmp/mmtpl_store.db")
        local_db = base_dir / "mmtpl_store.db"
        
        target = local_db
        if os.getenv("VERCEL"):
            if not tmp_db.exists() and local_db.exists():
                shutil.copyfile(local_db, tmp_db)
            if tmp_db.exists():
                target = tmp_db

        return create_engine(
            f"sqlite:///{target.as_posix()}",
            connect_args={"check_same_thread": False},
            pool_pre_ping=True
        )

engine = _create_robust_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
