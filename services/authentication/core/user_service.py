"""
User management service
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional

from models.user import User
from models.schemas import UserCreate, UserResponse
from core.security import hash_password, get_lockout_end_time
from config.settings import MAX_LOGIN_ATTEMPTS

class UserService:
    """Service for user management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if username already exists
        existing_user = self.db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        db_user = User(
            username=user_data.username,
            hashed_password=hashed_password,
            is_admin=user_data.is_admin
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def update_last_login(self, user: User) -> User:
        """Update user's last login time"""
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def increment_failed_attempts(self, user: User) -> User:
        """Increment failed login attempts"""
        user.failed_login_attempts += 1
        
        # Lock account if max attempts reached
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = get_lockout_end_time()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def unlock_user(self, user: User) -> User:
        """Unlock user account"""
        user.locked_until = None
        user.failed_login_attempts = 0
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def change_password(self, user: User, new_password: str) -> User:
        """Change user password"""
        user.hashed_password = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user(self, user: User, is_admin: Optional[bool] = None) -> User:
        """Update user information"""
        if is_admin is not None:
            user.is_admin = is_admin
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user: User) -> bool:
        """Delete user"""
        self.db.delete(user)
        self.db.commit()
        return True
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def get_user_count(self) -> int:
        """Get total user count"""
        return self.db.query(User).count()
