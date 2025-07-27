"""
Pydantic schemas for authentication service
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=8, max_length=128)
    is_admin: bool = False

class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)

class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    username: str
    is_admin: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    is_locked: bool = False

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    """Schema for password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

class UserUpdateRequest(BaseModel):
    """Schema for updating user information"""
    is_admin: Optional[bool] = None

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    service: str
    version: str
    database: str
    timestamp: datetime
