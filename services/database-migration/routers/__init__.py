"""
API Routers Package - Simplified
FastAPI router modules for organized endpoint management
"""
# Import only basic router and frontend_api for compatibility
from . import basic
from . import frontend_api

__all__ = [
    "basic",
    "frontend_api"
]
