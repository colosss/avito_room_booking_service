from pydantic_settings import BaseSettings, SettingsConfigDict
from src.infrastructure.database.db_config import DbSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MODE: str = "normal"

    @property
    def db(self) -> DbSettings:
        return DbSettings()

settings = Settings()
