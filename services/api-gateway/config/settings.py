"""
Configuration for API Gateway services and routes
"""
import os
from typing import Dict, Any

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://schemasage.vercel.app").split(",")

# Service configuration
SERVICES = {
    "schema-detection": {
        "url": os.getenv("SCHEMA_DETECTION_URL", "https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com"),
        "health_endpoint": "/health",
        "timeout": 30
    },
    "code-generation": {
        "url": os.getenv("CODE_GENERATION_URL", "https://schemasage-code-generation-56faa300323b.herokuapp.com"),
        "health_endpoint": "/health",
        "timeout": 30
    },
    "ai-chat": {
        "url": os.getenv("AI_CHAT_URL", "https://schemasage-ai-chat-b619aa05a30e.herokuapp.com"),
        "health_endpoint": "/health",
        "timeout": 30
    },
    "project-management": {
        "url": os.getenv("PROJECT_MANAGEMENT_URL", "https://schemasage-project-management-48496f02644b.herokuapp.com"),
        "health_endpoint": "/health",
        "timeout": 30
    },
    "authentication": {
        "url": os.getenv("AUTHENTICATION_URL", "https://schemasage-auth-9d6de1a32af9.herokuapp.com"),
        "health_endpoint": "/health",
        "timeout": 30
    }
}

# Route mappings with authentication requirements
ROUTE_MAPPINGS = {
    # Public routes (no auth required)
    "/api/auth/login": {"service": "authentication", "auth_required": False},
    "/api/auth/signup": {"service": "authentication", "auth_required": False},
    "/api/auth/refresh": {"service": "authentication", "auth_required": False},
    "/health": {"service": None, "auth_required": False},
    
    # Protected routes (auth required)
    "/api/schema/detect": {"service": "schema-detection", "auth_required": True},
    "/api/schema/detect-file": {"service": "schema-detection", "auth_required": True},
    "/api/schema/history": {"service": "schema-detection", "auth_required": True},
    "/api/code/generate": {"service": "code-generation", "auth_required": True},
    "/api/code/formats": {"service": "code-generation", "auth_required": True},
    "/api/code/templates": {"service": "code-generation", "auth_required": True},
    "/api/chat": {"service": "ai-chat", "auth_required": True},
    "/api/chat/history": {"service": "ai-chat", "auth_required": True},
    "/api/projects": {"service": "project-management", "auth_required": True},
    "/api/projects/upload": {"service": "project-management", "auth_required": True},
}

def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get configuration for a specific service."""
    return SERVICES.get(service_name, {})

def get_route_config(path: str) -> Dict[str, Any]:
    """Get route configuration for a specific path."""
    return ROUTE_MAPPINGS.get(path, {})

def is_protected_route(path: str) -> bool:
    """Check if a route requires authentication."""
    route_config = get_route_config(path)
    return route_config.get("auth_required", True)  # Default to protected
