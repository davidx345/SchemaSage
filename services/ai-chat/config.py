"""
Configuration for AI Chat Service
"""
import os
from typing import Dict, Any, Optional

class Settings:
    """Configuration settings for AI Chat service"""
    
    def __init__(self):
        # OpenAI Configuration
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # Gemini Configuration
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        # Service Configuration
        self.SERVICE_NAME = "ai-chat"
        self.SERVICE_VERSION = "1.0.0"
        # PORT and HOST are handled by Heroku via Procfile
        
        
        # Chat Configuration
        self.MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
        self.MAX_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "10"))
        
    def get_openai_headers(self) -> Dict[str, str]:
        """Get headers for OpenAI API requests"""
        return {
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
    def is_openai_configured(self) -> bool:
        """Check if OpenAI is properly configured"""
        return bool(self.OPENAI_API_KEY)
        
    def is_gemini_configured(self) -> bool:
        """Check if Gemini is properly configured"""
        return bool(self.GEMINI_API_KEY)

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()

settings = get_settings()
