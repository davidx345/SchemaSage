"""
Database Migration Service Main Application - Modularized
Enterprise-grade database migration platform with comprehensive features
"""
# Setup Python path for absolute imports
import sys
import os

# Add current directory to Python path to enable absolute imports
service_root = os.path.dirname(os.path.abspath(__file__))
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import routers
from routers import basic, etl, data_quality, monitoring, database_connectivity, universal_migration, frontend_api
from routers.migration_management import router as migration_management_router
from routers.simple_cloud_migration import router as simple_cloud_migration_router

# Temporarily disable complex cloud migration routers until imports are fixed
# from routers.cloud_migration import router as cloud_migration_router  
# from routers.advanced_cloud_migration import router as advanced_cloud_migration_router# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Database Migration Service - Enterprise Edition",
    description="Comprehensive database migration platform with AI-powered analysis, collaboration, and enterprise features",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://schemasage.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis removed for now - can be added back later for real-time collaboration features

# Include all routers
app.include_router(basic.router)
app.include_router(etl.router)
app.include_router(data_quality.router)
app.include_router(monitoring.router)
app.include_router(database_connectivity.router)
app.include_router(universal_migration.router)
app.include_router(frontend_api.router)
app.include_router(migration_management_router)
app.include_router(simple_cloud_migration_router)

# Temporarily disable complex cloud migration routers until imports are fixed
# app.include_router(cloud_migration_router)
# app.include_router(advanced_cloud_migration_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
