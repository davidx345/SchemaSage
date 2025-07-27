"""
API Routers Package

Contains all FastAPI routers for the project management service.
"""

from .projects import router as projects_router, stats_router
from .integrations import router as integrations_router
from .glossary import router as glossary_router, team_router
from .websocket import router as websocket_router

__all__ = [
    'projects_router',
    'stats_router',
    'integrations_router',
    'glossary_router',
    'team_router',
    'websocket_router'
]
