"""
Configuration for Code Generation Service
"""
import os
from enum import Enum
from typing import Dict, Any, Optional

class CodeGenFormat(str, Enum):
    """Supported code generation formats"""
    SQLALCHEMY = "sqlalchemy"
    PRISMA = "prisma"
    TYPEORM = "typeorm"
    DJANGO_ORM = "django_orm"
    SQL = "sql"
    JSON = "json"
    PYTHON_DATACLASSES = "python_dataclasses"
    DBML = "dbml"
    TYPESCRIPT_INTERFACES = "typescript_interfaces"

class Settings:
    """Configuration settings for Code Generation service"""
    
    def __init__(self):
        # Service Configuration
        self.SERVICE_NAME = "code-generation"
        self.SERVICE_VERSION = "1.0.0"
        self.PORT = int(os.getenv("CODE_GEN_PORT", "8083"))
        self.HOST = os.getenv("CODE_GEN_HOST", "0.0.0.0")
        
        # Template Configuration
        self.TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
        
        # Generation Configuration
        self.DEFAULT_VARCHAR_LENGTH = int(os.getenv("DEFAULT_VARCHAR_LENGTH", "255"))
        self.USE_MYPY_BY_DEFAULT = os.getenv("USE_MYPY_BY_DEFAULT", "true").lower() == "true"
        self.USE_VALIDATORS_BY_DEFAULT = os.getenv("USE_VALIDATORS_BY_DEFAULT", "true").lower() == "true"
        self.INCLUDE_STATISTICS_BY_DEFAULT = os.getenv("INCLUDE_STATISTICS_BY_DEFAULT", "true").lower() == "true"
        self.GENERATE_INDEXES_BY_DEFAULT = os.getenv("GENERATE_INDEXES_BY_DEFAULT", "true").lower() == "true"
        
        # OpenAI/Gemini for enhanced code generation (optional)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        
    def is_ai_enhanced(self) -> bool:
        """Check if AI enhancement is available"""
        return bool(self.OPENAI_API_KEY or self.GEMINI_API_KEY)

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()

settings = get_settings()
