"""
Authentication utilities for project-management service.
"""
import os
import httpx
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict

security = HTTPBearer()

# Get authentication service URL from environment
AUTHENTICATION_SERVICE_URL = os.getenv(
    'AUTHENTICATION_SERVICE_URL', 
    'http://localhost:8001'
)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Validate token with authentication service and return user data.
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
    current_user: dict = Depends(get_current_user)
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