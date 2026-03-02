"""Configuration for Schema Detection Service."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Service settings
    SERVICE_NAME: str = "schema-detection"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server settings - PORT and HOST are handled by Heroku via Procfile
    
    # Processing settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    MAX_SAMPLE_ROWS: int = Field(default=10000, env="MAX_SAMPLE_ROWS")
    
    # Timeout settings
    PROCESSING_TIMEOUT: int = Field(default=30, env="PROCESSING_TIMEOUT")  # seconds
    
    # Feature flags
    ENABLE_JSON5: bool = Field(default=True, env="ENABLE_JSON5")
    ENABLE_RELATIONSHIP_DETECTION: bool = Field(default=True, env="ENABLE_RELATIONSHIP_DETECTION")
    ENABLE_TYPE_INFERENCE: bool = Field(default=True, env="ENABLE_TYPE_INFERENCE")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Keys
    OPENAI_API_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    
    # Cloud Provisioning
    CREDENTIAL_ENCRYPTION_KEY: str = Field(default="", env="CREDENTIAL_ENCRYPTION_KEY")
    AWS_ACCESS_KEY: str = Field(default="", env="AWS_ACCESS_KEY")
    AWS_SECRET_KEY: str = Field(default="", env="AWS_SECRET_KEY")
    GCP_PROJECT_ID: str = Field(default="", env="GCP_PROJECT_ID")
    AZURE_SUBSCRIPTION_ID: str = Field(default="", env="AZURE_SUBSCRIPTION_ID")
    
    # Service URLs
    SERVICE_URL: str = Field(default="http://localhost:8001", env="SERVICE_URL")
    WEBSOCKET_URL: str = Field(default="ws://localhost:8001", env="WEBSOCKET_URL")
    
    # Background tasks
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://schema_user:password@postgres-schema:5432/schema_detection")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
