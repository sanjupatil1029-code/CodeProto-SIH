import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, ValidationInfo, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "NIRVAAN - Industrial Approval & Compliance Orchestrator"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = Field(default="super_secret_key_nirvaan_hackathon_2026_dev_only")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Databases
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/nirvaan")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Document Storage
    UPLOAD_DIR: str = Field(default="data/uploads")

    # Gemini AI API Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("UPLOAD_DIR", mode="after")
    @classmethod
    def create_upload_dir(cls, v: str) -> str:
        # Automatically create upload directory if it does not exist
        os.makedirs(v, exist_ok=True)
        return v


settings = Settings()
