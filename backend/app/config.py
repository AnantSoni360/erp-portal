import os
import shutil
from pathlib import Path
from pydantic_settings import BaseSettings

_BASE_DIR = Path(__file__).resolve().parent.parent
_ROOT_DIR = _BASE_DIR.parent
_DEFAULT_DB = _BASE_DIR / "mmtpl_store.db"

# Vercel Serverless environment handling
if os.getenv("VERCEL"):
    _TMP_DB = Path("/tmp/mmtpl_store.db")
    if not _TMP_DB.exists():
        if _DEFAULT_DB.exists():
            shutil.copyfile(_DEFAULT_DB, _TMP_DB)
        elif (_ROOT_DIR / "mmtpl_store.db").exists():
            shutil.copyfile(_ROOT_DIR / "mmtpl_store.db", _TMP_DB)
    _DB_TARGET = _TMP_DB
else:
    _DB_TARGET = _DEFAULT_DB

class Settings(BaseSettings):
    PROJECT_NAME: str = "MMTPL Store & Inventory Management ERP Portal"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "mmtpl-secret-key-store-inventory-management-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_DB_TARGET.as_posix()}")
    EXCEL_FILE_PATH: str = os.getenv("EXCEL_FILE_PATH", str((_ROOT_DIR / "MMTPL_Store_Tracker.xlsx").resolve()))

    class Config:
        case_sensitive = True

settings = Settings()
