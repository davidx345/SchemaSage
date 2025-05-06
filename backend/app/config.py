from pydantic_settings import BaseSettings
from typing import List, ClassVar, Optional, Any, Union
from functools import lru_cache
import os
import json
from pydantic import field_validator, ValidationError

def parse_list_value(v: Union[str, List[str]]) -> List[str]:
    """Parse a string value into a list, handling various formats:
    - Comma-separated string: "item1,item2"
    - Single value: "*"
    - JSON array string: '["item1","item2"]'
    """
    if isinstance(v, list):
        return v
    if not v:
        return []
    if v == "*":
        return ["*"]
    try:
        # Try parsing as JSON first
        parsed = json.loads(v)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except json.JSONDecodeError:
        # Fall back to comma-separated string
        return [x.strip() for x in v.split(",") if x.strip()]

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gemini API Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    # Use Gemini instead of OpenAI
    USE_GEMINI: bool = True
    
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Model Parameters
    MAX_NEW_TOKENS: int = 512
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    REPETITION_PENALTY: float = 1.1
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

    # MongoDB Settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "schema_sage"
    MONGODB_PROJECTS_COLLECTION: str = "projects"
    MONGODB_SCHEMAS_COLLECTION: str = "schemas"

    # Configuration
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env

    # Validators
    @field_validator("ALLOWED_HOSTS", "ALLOWED_ORIGINS", mode="before")
    def validate_list_fields(cls, v: Any) -> List[str]:
        """Validate and parse list fields from environment variables"""
        try:
            return parse_list_value(v)
        except Exception as e:
            raise ValueError(f"Failed to parse list value: {str(e)}")  # Fixed missing closing parenthesis

@lru_cache()
def get_settings() -> Settings:
    """Get settings with detailed error handling"""
    try:
        return Settings()
    except ValidationError as e:
        # Create a more user-friendly error message
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"- {field}: {msg}")
        
        error_msg = "Failed to load settings:\n" + "\n".join(errors)
        error_msg += "\n\nPlease check your .env file and ensure all values are in the correct format:"
        error_msg += "\n- Lists should be comma-separated: KEY=value1,value2 or KEY=[\"value1\",\"value2\"]"
        error_msg += "\n- Single values: KEY=value"
        error_msg += "\n- Numbers: KEY=123"
        error_msg += "\n- Booleans: KEY=true or KEY=false"
        
        raise RuntimeError(error_msg)

# Create a settings instance to be imported by other modules
settings = get_settings()