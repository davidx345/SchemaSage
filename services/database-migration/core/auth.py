"""
JWT Authentication Service for Database Migration Service
Integrates with SchemaSage authentication service
Provides user context, permissions, and security middleware
"""
import jwt
import httpx
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class AuthConfig:
    """Authentication configuration"""
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_jwt_secret_key_not_for_production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Authentication Service Configuration
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "https://schemasage-authentication-6c4c5cdafe76.herokuapp.com")
    SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "dev_service_key")
    
    # Cache settings
    USER_CACHE_TTL_SECONDS = int(os.getenv("USER_CACHE_TTL_SECONDS", "300"))  # 5 minutes
    
    # Rate limiting
    MAX_AUTH_REQUESTS_PER_MINUTE = int(os.getenv("MAX_AUTH_REQUESTS_PER_MINUTE", "60"))


@dataclass
class UserContext:
    """User context from JWT token"""
    user_id: str
    username: str
    email: str
    role: str = "user"
    permissions: List[str] = None
    is_admin: bool = False
    subscription_plan: str = "free"
    organization_id: Optional[str] = None
    team_ids: List[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
        if self.team_ids is None:
            self.team_ids = []
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return self.is_admin or permission in self.permissions
    
    def can_access_team_resources(self, team_id: str) -> bool:
        """Check if user can access team resources"""
        return self.is_admin or team_id in self.team_ids
    
    def get_quota_multiplier(self) -> int:
        """Get quota multiplier based on subscription plan"""
        multipliers = {
            "free": 1,
            "pro": 5,
            "enterprise": 20,
            "unlimited": 100
        }
        return multipliers.get(self.subscription_plan, 1)


class JWTAuthService:
    """
    JWT Authentication service with user context management
    """
    
    def __init__(self):
        self.config = AuthConfig()
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self.user_cache: Dict[str, tuple] = {}  # (user_context, expiry_time)
        self.security = HTTPBearer(auto_error=False)
    
    async def verify_token(self, token: str) -> Optional[UserContext]:
        """
        Verify JWT token and extract user context
        """
        try:
            # First try local verification
            payload = jwt.decode(
                token, 
                self.config.JWT_SECRET_KEY, 
                algorithms=[self.config.JWT_ALGORITHM]
            )
            
            user_id = payload.get("user_id") or payload.get("sub")
            if not user_id:
                return None
            
            # Check cache first
            cached_user = self._get_cached_user(user_id)
            if cached_user:
                return cached_user
            
            # Create user context from token
            user_context = UserContext(
                user_id=user_id,
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                role=payload.get("role", "user"),
                permissions=payload.get("permissions", []),
                is_admin=payload.get("is_admin", False),
                subscription_plan=payload.get("subscription_plan", "free"),
                organization_id=payload.get("organization_id"),
                team_ids=payload.get("team_ids", [])
            )
            
            # Cache user context
            self._cache_user(user_id, user_context)
            
            return user_context
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    async def verify_with_auth_service(self, token: str) -> Optional[UserContext]:
        """
        Verify token with authentication service (fallback/validation)
        """
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Service-Key": self.config.SERVICE_API_KEY
            }
            
            response = await self.http_client.get(
                f"{self.config.AUTH_SERVICE_URL}/api/auth/verify",
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return UserContext(
                    user_id=user_data["user_id"],
                    username=user_data.get("username", ""),
                    email=user_data.get("email", ""),
                    role=user_data.get("role", "user"),
                    permissions=user_data.get("permissions", []),
                    is_admin=user_data.get("is_admin", False),
                    subscription_plan=user_data.get("subscription_plan", "free"),
                    organization_id=user_data.get("organization_id"),
                    team_ids=user_data.get("team_ids", [])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Auth service verification failed: {e}")
            return None
    
    def _get_cached_user(self, user_id: str) -> Optional[UserContext]:
        """Get user from cache if not expired"""
        if user_id in self.user_cache:
            user_context, expiry = self.user_cache[user_id]
            if datetime.utcnow() < expiry:
                return user_context
            else:
                # Remove expired entry
                del self.user_cache[user_id]
        return None
    
    def _cache_user(self, user_id: str, user_context: UserContext):
        """Cache user context with TTL"""
        expiry = datetime.utcnow() + timedelta(seconds=self.config.USER_CACHE_TTL_SECONDS)
        self.user_cache[user_id] = (user_context, expiry)
    
    async def get_current_user_simple(self, request: Request) -> Optional[UserContext]:
        """
        Simple user extraction without HTTPBearer dependency
        For endpoints that need to handle anonymous users gracefully
        """
        token = None
        
        # Debug authentication headers
        auth_headers = {
            'authorization': request.headers.get('authorization'),
            'x-auth-token': request.headers.get('x-auth-token'),
            'x-user-id': request.headers.get('x-user-id'),
            'x-username': request.headers.get('x-username'),
            'x-user-email': request.headers.get('x-user-email')
        }
        logger.info(f"🔍 Auth headers received: {auth_headers}")
        
        # Method 1: Authorization header (Bearer token)
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            logger.info(f"🔑 Using Bearer token authentication")
        
        # Method 2: Custom header from API Gateway
        elif request.headers.get("x-auth-token"):
            token = request.headers.get("x-auth-token")
            logger.info(f"🔑 Using x-auth-token authentication")
        
        # Method 3: User ID directly from API Gateway (simplified)
        elif request.headers.get("x-user-id"):
            user_id = request.headers.get("x-user-id")
            logger.info(f"🔑 Using direct user ID authentication: {user_id}")
            # Create minimal user context
            return UserContext(
                user_id=user_id,
                username=request.headers.get("x-username", ""),
                email=request.headers.get("x-user-email", ""),
                role=request.headers.get("x-user-role", "user"),
                is_admin=request.headers.get("x-user-admin", "").lower() == "true"
            )
        
        if token:
            user_context = await self.verify_token(token)
            if user_context:
                logger.info(f"✅ Token authentication successful for user: {user_context.user_id}")
                return user_context
            else:
                logger.warning(f"❌ Token authentication failed")
        
        # Return anonymous user for public endpoints
        logger.info(f"⚠️ No authentication provided, returning anonymous user")
        return UserContext(
            user_id="anonymous",
            username="anonymous",
            email=""
        )

    async def get_current_user(
        self, 
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> Optional[UserContext]:
        """
        Extract current user from request
        Supports multiple authentication methods for flexibility
        """
        token = None
        
        # Debug authentication headers
        auth_headers = {
            'authorization': request.headers.get('authorization'),
            'x-auth-token': request.headers.get('x-auth-token'),
            'x-user-id': request.headers.get('x-user-id'),
            'x-username': request.headers.get('x-username'),
            'x-user-email': request.headers.get('x-user-email')
        }
        logger.info(f"🔍 Auth headers received: {auth_headers}")
        
        # Method 1: Authorization header (Bearer token)
        if credentials:
            token = credentials.credentials
            logger.info(f"🔑 Using Bearer token authentication")
        
        # Method 2: Custom header from API Gateway
        elif request.headers.get("x-auth-token"):
            token = request.headers.get("x-auth-token")
            logger.info(f"🔑 Using x-auth-token authentication")
        
        # Method 3: User ID directly from API Gateway (simplified)
        elif request.headers.get("x-user-id"):
            user_id = request.headers.get("x-user-id")
            logger.info(f"🔑 Using direct user ID authentication: {user_id}")
            # Create minimal user context
            return UserContext(
                user_id=user_id,
                username=request.headers.get("x-username", ""),
                email=request.headers.get("x-user-email", ""),
                role=request.headers.get("x-user-role", "user"),
                is_admin=request.headers.get("x-user-admin", "").lower() == "true"
            )
        
        if token:
            user_context = await self.verify_token(token)
            if user_context:
                logger.info(f"✅ Token authentication successful for user: {user_context.user_id}")
                return user_context
            else:
                logger.warning(f"❌ Token authentication failed")
        
        # Return anonymous user for public endpoints
        logger.info(f"⚠️ No authentication provided, returning anonymous user")
        return UserContext(
            user_id="anonymous",
            username="anonymous",
            email=""
        )
    
    async def require_authentication(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer())
    ) -> UserContext:
        """
        Require valid authentication (raises exception if not authenticated)
        """
        user = await self.get_current_user(request, credentials)
        
        if not user or user.user_id == "anonymous":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
    
    async def get_current_user_from_request(self, request: Request) -> Optional[UserContext]:
        """Get current user directly from request without HTTPBearer dependency"""
        try:
            # Extract authorization header manually
            auth_header = request.headers.get("authorization")
            if not auth_header:
                return None
            
            # Check if it's a Bearer token
            if not auth_header.startswith("Bearer "):
                return None
            
            # Extract token
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Verify token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            
            if username is None:
                return None
            
            # Create user context
            user = UserContext(
                user_id=username,
                username=username,
                email=payload.get("email", f"{username}@example.com"),
                is_admin=payload.get("is_admin", False)
            )
            
            return user
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting user from request: {e}")
            return None
    
    def require_permission(self, permission: str):
        """
        Decorator to require specific permission
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user from kwargs (should be injected by dependency)
                user = kwargs.get('current_user')
                
                if not user or not user.has_permission(permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{permission}' required"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_admin(self):
        """
        Decorator to require admin access
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = kwargs.get('current_user')
                
                if not user or not user.is_admin:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Admin access required"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


class AuthMiddleware:
    """
    Authentication middleware for logging and audit
    """
    
    def __init__(self, auth_service: JWTAuthService):
        self.auth_service = auth_service
    
    async def log_auth_event(
        self,
        request: Request,
        user: Optional[UserContext],
        action: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log authentication events for audit"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user.user_id if user else "anonymous",
            "action": action,
            "success": success,
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
            "endpoint": str(request.url.path),
            "method": request.method,
            "details": details or {}
        }
        
        # In production, send to centralized logging
        if success:
            logger.info(f"Auth success: {action} by {user.user_id if user else 'anonymous'}")
        else:
            logger.warning(f"Auth failure: {action} - {details}")


# Singleton instances
auth_service = JWTAuthService()
auth_middleware = AuthMiddleware(auth_service)

# Dependency functions for FastAPI
async def get_current_user_simple(request: Request) -> Optional[UserContext]:
    """FastAPI dependency for getting current user (simple version without HTTPBearer)"""
    return await auth_service.get_current_user_simple(request)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[UserContext]:
    """FastAPI dependency for getting current user"""
    return await auth_service.get_current_user(request, credentials)

async def require_authentication(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer())
) -> UserContext:
    """FastAPI dependency for requiring authentication"""
    return await auth_service.require_authentication(request, credentials)

def get_user_id_from_context(user: UserContext = Depends(get_current_user)) -> str:
    """Extract user ID from authenticated user context"""
    return user.user_id if user else "anonymous"