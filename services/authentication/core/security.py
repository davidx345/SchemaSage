"""
Authentication and security utilities
"""
import jwt
import time
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from config.settings import (
    JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
    MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES, RATE_LIMIT_PER_MINUTE
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting store (use Redis in production)
login_attempts: Dict[str, List[float]] = {}

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
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

def is_rate_limited(identifier: str) -> bool:
    """Check if identifier is rate limited"""
    current_time = time.time()
    minute_ago = current_time - 60
    
    if identifier in login_attempts:
        login_attempts[identifier] = [
            t for t in login_attempts[identifier] if t > minute_ago
        ]
    else:
        login_attempts[identifier] = []
    
    if len(login_attempts[identifier]) >= RATE_LIMIT_PER_MINUTE:
        return True
    
    login_attempts[identifier].append(current_time)
    return False

def validate_password_strength(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    
    # Check for at least one uppercase, lowercase, digit, and special character
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_upper and has_lower and has_digit and has_special

def get_lockout_end_time() -> datetime:
    """Get the lockout end time"""
    return datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
