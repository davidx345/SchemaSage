"""
Authentication utilities for project-management service.
"""
import os
import jwt
import httpx
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict

security = HTTPBearer()

# Get authentication service URL from environment
AUTHENTICATION_SERVICE_URL = os.getenv(
    'AUTHENTICATION_SERVICE_URL', 
    'http://localhost:8001'
)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user ID from JWT token"""
    try:
        # Get JWT secret from environment
        jwt_secret = os.getenv("JWT_SECRET_KEY", "dev_jwt_secret_key_not_for_production")
        
        # Decode JWT token
        token = credentials.credentials
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        
        # Extract user ID
        user_id = payload.get("user_id") or payload.get("sub") or payload.get("id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: user ID not found"
            )
        
        return str(user_id)
        
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[str]:
    """Extract user ID from JWT token, but don't fail if no token provided"""
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None

async def get_current_user_legacy(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Legacy method: Validate token with authentication service and return user data.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Call authentication service to validate token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTHENTICATION_SERVICE_URL}/me",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid or expired token"
                )
            
            return response.json()
            
    except httpx.RequestError:
        # Fallback for development when auth service is not available
        return {
            "id": "dev-user-001",
            "email": "dev@example.com",
            "is_admin": True,
            "tenant_id": "default-tenant"
        }
    except Exception as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Authentication failed: {str(e)}"
        )

async def get_current_admin_user(
    current_user: dict = Depends(get_current_user_legacy)
) -> dict:
    """
    Ensure current user has admin privileges.
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403, 
            detail="Admin privileges required"
        )
    return current_user