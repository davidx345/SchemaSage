"""Configuration for Schema Detection Service."""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Service settings
    SERVICE_NAME: str = "schema-detection"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8001, env="PORT")
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
