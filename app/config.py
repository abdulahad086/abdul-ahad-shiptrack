from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_ENV: str = "local"
    LOG_LEVEL: str = "INFO"
    API_KEY: str
    AUDIT_LOG_PATH: str

    @field_validator("API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("API_KEY must not be empty or whitespace only")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()