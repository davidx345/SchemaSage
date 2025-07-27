"""
Authentication service main module
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any

from models.user import User
from models.schemas import LoginRequest, TokenResponse, UserResponse
from core.security import verify_password, create_access_token, is_rate_limited
from core.user_service import UserService
from config.settings import JWT_EXPIRATION_HOURS

class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
    
    def authenticate_user(self, login_data: LoginRequest, client_ip: str) -> TokenResponse:
        """Authenticate user and return token"""
        
        # Check rate limiting
        if is_rate_limited(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Get user
        user = self.user_service.get_user_by_username(login_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is locked
        if user.is_locked():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is locked due to too many failed login attempts"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            # Increment failed attempts
            self.user_service.increment_failed_attempts(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Update last login
        user = self.user_service.update_last_login(user)
        
        # Create token
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "is_admin": user.is_admin
        }
        access_token = create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user=UserResponse(
                id=user.id,
                username=user.username,
                is_admin=user.is_admin,
                created_at=user.created_at,
                last_login=user.last_login,
                failed_login_attempts=user.failed_login_attempts,
                is_locked=user.is_locked()
            )
        )
    
    def get_current_user(self, token_payload: Dict[str, Any]) -> User:
        """Get current user from token payload"""
        username = token_payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = self.user_service.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    def refresh_token(self, token_payload: Dict[str, Any]) -> TokenResponse:
        """Refresh access token"""
        user = self.get_current_user(token_payload)
        
        # Create new token
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "is_admin": user.is_admin
        }
        access_token = create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user=UserResponse(
                id=user.id,
                username=user.username,
                is_admin=user.is_admin,
                created_at=user.created_at,
                last_login=user.last_login,
                failed_login_attempts=user.failed_login_attempts,
                is_locked=user.is_locked()
            )
        )
