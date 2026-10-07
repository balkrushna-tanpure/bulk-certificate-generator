import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'certificates.db'}"
    
    # Storage
    STORAGE_DIR: Path = BASE_DIR / "storage" / "certificates"
    
    # Concurrency for bulk generation thread pool
    MAX_WORKER_THREADS: int = 4

    model_config = {"env_file": ".env", "extra": "allow"}

settings = Settings()

# Ensure storage directory exists
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
