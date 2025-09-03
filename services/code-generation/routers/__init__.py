"""
API Routers Package for Code Generation Service

Contains all FastAPI routers for the code generation service.
"""

from .compliance_generation import router as compliance_generation_router

__all__ = [
    'compliance_generation_router'
]
