# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DB_HOST: str| None = None
    DB_PORT: int =5432
    DB_NAME: str| None = None
    DB_USER: str| None = None
    DB_PASSWORD: str| None = None

    ONE_TIME_PASSWORD: str| None = None

    SMTP_HOST: str| None = None
    SMTP_PORT: int| None = None
    SMTP_USER: str| None = None
    SMTP_PASSWORD: str| None = None
    SMTP_FROM: str| None = None

    RESET_LINK_BASE: str| None = None
    RESET_TOKEN_LIFETIME_MINUTES: int =60  # default to 60

    IMAGE_UPLOAD_DIR: str| None = None
    MAX_FILE_SIZE_MB: int =8

    SECRET_KEY: str| None = None            # added for JWT secret
    ALGORITHM: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60000  # default to 60 if not set

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()