"""Application configuration loaded from the .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads GROQ_API_KEY, GROQ_MODEL, and LOG_LEVEL from the environment / .env file."""
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
