from fastapi import FastAPI, HTTPException, Depends, Security, Request, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
import jwt
import os
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import secrets

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/schemasage")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_jwt_secret_key_not_for_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Rate limiting store (use Redis in production)
login_attempts: Dict[str, List[float]] = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=8, max_length=128)
    is_admin: bool = False
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)

class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime
    last_login: datetime = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

def validate_password_strength(password: str) -> None:
    """Validate password meets security requirements."""
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character")

def is_rate_limited(identifier: str) -> bool:
    """Check if identifier is rate limited for login attempts."""
    current_time = time.time()
    minute_ago = current_time - 60
    
    # Clean old entries
    if identifier in login_attempts:
        login_attempts[identifier] = [t for t in login_attempts[identifier] if t > minute_ago]
    else:
        login_attempts[identifier] = []
    
    # Check if limit exceeded (5 attempts per minute)
    if len(login_attempts[identifier]) >= 5:
        return True
    
    # Add current attempt
    login_attempts[identifier].append(current_time)
    return False

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_user(db: Session, user: UserCreate):
    validate_password_strength(user.password)
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username, 
        hashed_password=hashed_password, 
        is_admin=user.is_admin,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str, client_ip: str):
    # Check if user is locked
    user = db.query(User).filter(User.username == username).first()
    if user and user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until}"
        )
    
    # Verify credentials
    if not user or not pwd_context.verify(password, user.hashed_password):
        # Log failed attempt
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            db.commit()
        
        # Consistent response time to prevent timing attacks
        time.sleep(0.5)
        return None
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

app = FastAPI(
    title="Authentication Service",
    description="Secure authentication and authorization service",
    version="1.0.0"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://schemasage.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.post("/signup", response_model=Token)
def signup(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host
    
    # Rate limiting
    if is_rate_limited(f"signup:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signup attempts. Please try again later."
        )
    
    # Check if user exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    try:
        db_user = create_user(db, user)
        access_token = create_access_token({"sub": db_user.username, "is_admin": db_user.is_admin})
        
        logger.info(f"New user registered: {user.username} from {client_ip}")
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_in": JWT_EXPIRATION_HOURS * 3600
        }
    except Exception as e:
        logger.error(f"Signup error for {user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, request: Request = None, db: Session = Depends(get_db)):
    client_ip = request.client.host if request else "unknown"
    
    # Rate limiting
    if is_rate_limited(f"login:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    try:
        user = authenticate_user(db, user_data.username, user_data.password, client_ip)
        if not user:
            logger.warning(f"Failed login attempt for {user_data.username} from {client_ip}")
            raise HTTPException(
                status_code=401, 
                detail="Incorrect username or password"
            )
        
        access_token = create_access_token({"sub": user.username, "is_admin": user.is_admin})
        
        logger.info(f"Successful login: {user.username} from {client_ip}")
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        return TokenResponse(
            access_token=access_token, 
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user=user_response
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {user_data.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# OAuth2 compatibility endpoint
@app.post("/token", response_model=TokenResponse)
def oauth_login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db: Session = Depends(get_db)):
    user_data = UserLogin(username=form_data.username, password=form_data.password)
    return login(user_data, request, db)

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """Dependency to ensure current user is an admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Admin privileges required"
        )
    return current_user

@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username, 
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@app.post("/refresh-token", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh the access token for authenticated users"""
    access_token = create_access_token({"sub": current_user.username, "is_admin": current_user.is_admin})
    
    user_response = UserResponse(
        id=current_user.id,
        username=current_user.username,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user=user_response
    )

@app.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint (client should discard token)"""
    logger.info(f"User {current_user.username} logged out")
    return {"message": "Successfully logged out"}

@app.get("/users", response_model=List[UserResponse])
def list_users(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    """Admin endpoint to list all users"""
    users = db.query(User).all()
    return [UserResponse(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login
    ) for user in users]

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy", 
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        # Don't fail startup if database is not available
        # This allows the service to start even if DB is temporarily unavailable
    logger.info("Authentication service started successfully")
