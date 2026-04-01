from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel

class DbSettings(BaseModel):
    user: str = "user"
    password: str = "password"
    host: str = "localhost"
    port: int = 5432
    name: str = "database"
    echo: bool = False

    @property
    def url(self)->str:
        db_prefix="postgresql+asyncpg"
        return f"{db_prefix}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="_", case_sensitive=False)
    db: DbSettings = DbSettings()
    mode: str = "normal"

settings = Settings()