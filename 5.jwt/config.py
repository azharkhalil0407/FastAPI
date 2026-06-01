from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    model_config = {"env_file": str(BASE_DIR / ".env")}

setting = Settings()