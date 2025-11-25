"""
API Routers Package

Contains all FastAPI routers for the project management service.
"""

from .integrations import router as integrations_router
from .glossary import router as glossary_router
from .websocket import router as websocket_router
from .upload import router as upload_router
from .compliance import router as compliance_router

__all__ = [
    'integrations_router',
    'glossary_router',
    'websocket_router',
    'upload_router',
    'compliance_router'
]
