"""Security middleware and utilities for SchemaSage services."""

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
import time
import hashlib
from typing import Dict, Optional, List
import logging
from functools import wraps
import os

logger = logging.getLogger(__name__)

# Rate limiting store (use Redis in production)
RATE_LIMIT_STORE: Dict[str, List[float]] = {}

class SecurityConfig:
    """Security configuration."""
    
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_jwt_secret_key_not_for_production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

security_config = SecurityConfig()

class RateLimiter:
    """Rate limiting implementation."""
    
    @staticmethod
    def is_rate_limited(identifier: str, limit_per_minute: int = None) -> bool:
        """Check if identifier is rate limited."""
        if limit_per_minute is None:
            limit_per_minute = security_config.RATE_LIMIT_PER_MINUTE
            
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old entries
        if identifier in RATE_LIMIT_STORE:
            RATE_LIMIT_STORE[identifier] = [
                t for t in RATE_LIMIT_STORE[identifier] if t > minute_ago
            ]
        else:
            RATE_LIMIT_STORE[identifier] = []
        
        # Check if limit exceeded
        if len(RATE_LIMIT_STORE[identifier]) >= limit_per_minute:
            return True
        
        # Add current request
        RATE_LIMIT_STORE[identifier].append(current_time)
        return False

class SecurityMiddleware:
    """Security middleware for FastAPI applications."""
    
    @staticmethod
    def setup_cors(app):
        """Setup CORS middleware."""
        app.add_middleware(
            CORSMiddleware,
            allow_origins=security_config.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )
    
    @staticmethod
    async def rate_limit_middleware(request: Request, call_next):
        """Rate limiting middleware."""
        client_ip = request.client.host
        
        # Create identifier (IP + endpoint)
        identifier = f"{client_ip}:{request.url.path}"
        
        if RateLimiter.is_rate_limited(identifier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        response = await call_next(request)
        return response

class TokenValidator:
    """JWT token validation."""
    
    @staticmethod
    def verify_token(token: str) -> Dict:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token, 
                security_config.JWT_SECRET_KEY, 
                algorithms=[security_config.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_file_size(file_size: int) -> None:
        """Validate file size."""
        if file_size > security_config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum limit of {security_config.MAX_FILE_SIZE} bytes"
            )
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Sanitize and validate filename."""
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename cannot be empty"
            )
        
        # Remove path traversal attempts
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Validate file extension
        allowed_extensions = ['.csv', '.json', '.xml', '.sql', '.txt']
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return filename
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize text input."""
        if not text:
            return ""
        
        # Limit length
        if len(text) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input too long. Maximum {max_length} characters allowed."
            )
        
        # Remove dangerous patterns
        dangerous_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Input contains potentially dangerous content"
                )
        
        return text.strip()

def require_auth(func):
    """Decorator for requiring authentication."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        payload = TokenValidator.verify_token(token)
        
        # Add user info to request state
        request.state.user = payload
        
        return await func(request, *args, **kwargs)
    return wrapper

def require_admin(func):
    """Decorator for requiring admin role."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if not hasattr(request.state, 'user'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user = request.state.user
        if not user.get('is_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        return await func(request, *args, **kwargs)
    return wrapper
