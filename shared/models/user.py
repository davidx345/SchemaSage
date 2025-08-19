"""User-related models."""

from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID
from .base import BaseModel


class UserRole(str, Enum):
    """User roles."""
    
    USER = "user"
    ADMIN = "admin"
    PREMIUM = "premium"


class UserStatus(str, Enum):
    """User status."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserModel(BaseModel):
    """User model - integrates with Supabase Auth."""
    
    # Note: id comes from Supabase auth.users table as UUID
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    
    # Profile information
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    # Preferences
    preferences: Dict[str, Any] = {}
    
    # Usage statistics (populated from related tables)
    project_count: int = 0
    storage_used: int = 0  # in bytes
    last_login: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""
    
    user: UserModel
    permissions: List[str] = []
    subscription_info: Optional[Dict[str, Any]] = None


class UserLoginRequest(BaseModel):
    """User login request."""
    
    email: str
    password: str


class UserRegisterRequest(BaseModel):
    """User registration request."""
    
    email: str
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """User update request."""
    
    full_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class AuthTokenResponse(BaseModel):
    """Authentication token response."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    user: UserModel
