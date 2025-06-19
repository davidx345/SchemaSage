"""
Configuration for Project Management Service
"""
import os

class Settings:
    """Configuration settings for Project Management service"""
    
    def __init__(self):
        # Service Configuration
        self.SERVICE_NAME = "project-management"
        self.SERVICE_VERSION = "1.0.0"
        self.PORT = int(os.getenv("PROJECT_MGMT_PORT", "8084"))
        self.HOST = os.getenv("PROJECT_MGMT_HOST", "0.0.0.0")
        
        # Database Configuration (if needed)
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./projects.db")
        
        # File Storage Configuration
        self.UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
        self.ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "csv,json,sql,xlsx").split(",")

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()

settings = get_settings()
