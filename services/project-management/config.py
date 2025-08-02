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
        # PORT and HOST are handled by Heroku via Procfile
        
        # Database Configuration (if needed)
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./projects.db")
        
        # AWS S3 Configuration for file storage
        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        self.S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
        
        # File Configuration
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
        self.ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "csv,json,sql,xlsx").split(",")
        
        # Use S3 if configured, otherwise fall back to local storage
        self.USE_S3 = bool(self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY and self.S3_BUCKET_NAME)
        self.UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads") if not self.USE_S3 else None

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()

settings = get_settings()
