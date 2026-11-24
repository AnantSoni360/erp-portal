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

_DB_ENV = os.getenv("DATABASE_URL")
if _DB_ENV:
    if _DB_ENV.startswith("postgres://"):
        _RESOLVED_DB_URL = _DB_ENV.replace("postgres://", "postgresql://", 1)
    else:
        _RESOLVED_DB_URL = _DB_ENV

    # Auto-resolve direct Supabase URL to IPv4 Transaction Pooler URL
    import re
    m = re.match(r"postgresql://([^:]+):([^@]+)@db\.([a-z0-9]+)\.supabase\.co:(\d+)/(.+)", _RESOLVED_DB_URL)
    if m:
        _user = m.group(1)
        _pwd = m.group(2)
        _proj = m.group(3)
        _db = m.group(5).split("?")[0]
        _RESOLVED_DB_URL = f"postgresql://{_user}.{_proj}:{_pwd}@aws-0-ap-southeast-2.pooler.supabase.com:6543/{_db}"

    # Ensure sslmode=require for cloud PostgreSQL
    if "sslmode=" not in _RESOLVED_DB_URL:
        _sep = "&" if "?" in _RESOLVED_DB_URL else "?"
        _RESOLVED_DB_URL = f"{_RESOLVED_DB_URL}{_sep}sslmode=require"
else:
    _RESOLVED_DB_URL = f"sqlite:///{_DB_TARGET.as_posix()}"

# Critical: Update os.environ so Pydantic BaseSettings uses the resolved URL
os.environ["DATABASE_URL"] = _RESOLVED_DB_URL

class Settings(BaseSettings):
    PROJECT_NAME: str = "MMTPL Store & Inventory Management ERP Portal"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "mmtpl-secret-key-store-inventory-management-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    DATABASE_URL: str = _RESOLVED_DB_URL
    EXCEL_FILE_PATH: str = os.getenv("EXCEL_FILE_PATH", str((_ROOT_DIR / "MMTPL_Store_Tracker.xlsx").resolve()))

    class Config:
        case_sensitive = True

settings = Settings()
settings.DATABASE_URL = _RESOLVED_DB_URL
