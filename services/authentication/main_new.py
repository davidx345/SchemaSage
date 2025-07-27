"""
Authentication Microservice
Handles user authentication and authorization
"""
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from contextlib import asynccontextmanager
from datetime import datetime

# Import modular components
from config.settings import CORS_ORIGINS, SERVICE_NAME, SERVICE_VERSION
from models.user import get_database, create_tables, User
from models.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse, 
    LoginRequest, PasswordChangeRequest, UserUpdateRequest, HealthResponse
)
from core.auth_service import AuthService
from core.user_service import UserService
from core.security import verify_token

logger = logging.getLogger(__name__)
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Authentication Service starting up...")
    create_tables()
    logger.info("Database tables created/verified")
    yield
    # Shutdown
    logger.info("Authentication Service shutting down...")

app = FastAPI(
    title=SERVICE_NAME,
    description="Microservice for user authentication and authorization",
    version=SERVICE_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database)
) -> User:
    """Get current authenticated user"""
    token_payload = verify_token(credentials.credentials)
    auth_service = AuthService(db)
    return auth_service.get_current_user(token_payload)

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@app.post("/signup", response_model=UserResponse)
async def signup(
    user_data: UserCreate,
    db: Session = Depends(get_database)
):
    """Register a new user"""
    user_service = UserService(db)
    user = user_service.create_user(user_data)
    return UserResponse(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts,
        is_locked=user.is_locked()
    )

@app.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_database)
):
    """Authenticate user and return token"""
    client_ip = request.client.host
    auth_service = AuthService(db)
    return auth_service.authenticate_user(login_data, client_ip)

@app.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Refresh access token"""
    auth_service = AuthService(db)
    token_payload = {
        "sub": current_user.username,
        "user_id": current_user.id,
        "is_admin": current_user.is_admin
    }
    return auth_service.refresh_token(token_payload)

@app.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        failed_login_attempts=current_user.failed_login_attempts,
        is_locked=current_user.is_locked()
    )

@app.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Change user password"""
    from core.security import verify_password
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Change password
    user_service = UserService(db)
    user_service.change_password(current_user, password_data.new_password)
    
    return {"message": "Password changed successfully"}

@app.get("/users", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get all users (admin only)"""
    user_service = UserService(db)
    users = user_service.get_all_users(skip, limit)
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_login=user.last_login,
            failed_login_attempts=user.failed_login_attempts,
            is_locked=user.is_locked()
        )
        for user in users
    ]

@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_database)):
    """Health check endpoint"""
    try:
        # Test database connection
        user_service = UserService(db)
        user_count = user_service.get_user_count()
        
        return HealthResponse(
            status="healthy",
            service=SERVICE_NAME,
            version=SERVICE_VERSION,
            database=f"connected ({user_count} users)",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
