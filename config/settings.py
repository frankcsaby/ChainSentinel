from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "ChainSentinel Enterprise"
    VERSION: str = "1.0.0"
    MODEL_NAME: str = "llama3.1"  # Vagy "mistral"
    
    # Útvonalak (dinamikusan)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = DATA_DIR / "logs"
    REPORT_DIR: Path = DATA_DIR / "reports"
    KNOWLEDGE_BASE_DIR: Path = DATA_DIR / "knowledge_base"

    # API Limitek
    MAX_TOKENS: int = 4096
    API_TIMEOUT: int = 30

    class Config:
        model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# Automatikus mappa létrehozás
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORT_DIR.mkdir(parents=True, exist_ok=True)
settings.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)