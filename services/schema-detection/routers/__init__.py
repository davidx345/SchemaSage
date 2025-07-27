"""
API Routers Package for Schema Detection Service

Contains all FastAPI routers for the schema detection service.
"""

from .detection import router as detection_router
from .lineage import router as lineage_router
from .history import router as history_router

__all__ = [
    'detection_router',
    'lineage_router', 
    'history_router'
]
