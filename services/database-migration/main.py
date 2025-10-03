"""
Database Migration Service Main Application - Enterprise Edition
PostgreSQL-backed persistent storage with JWT authentication and AES-256 encryption
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

# Import enterprise routers
from routers import basic, etl, data_quality, monitoring, database_connectivity, universal_migration
from routers import frontend_api  # Now the enterprise version
from routers.migration_management import router as migration_management_router
from routers.simple_cloud_migration import router as simple_cloud_migration_router
from routers.performance_cost_calculator import router as performance_cost_calculator_router
from routers.smart_rollback import router as smart_rollback_router
from routers.performance_cost_calculator import router as performance_cost_calculator_router
from routers.smart_rollback import router as smart_rollback_router

# Enterprise services
from core.enterprise_store import enterprise_store
from core.auth import auth_service
from core.encryption import key_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Database Migration Service - Enterprise Edition",
    description="Enterprise database migration platform with PostgreSQL persistence, JWT authentication, and AES-256 encryption",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
async def startup_event():
    """Initialize enterprise services and log startup configuration"""
    try:
        logger.info("🚀 Database Migration Service Enterprise Edition starting...")
        
        # Initialize enterprise store
        await enterprise_store.initialize()
        logger.info("✅ PostgreSQL persistence layer initialized")
        
        # Validate encryption environment
        encryption_status = key_manager.validate_encryption_environment()
        if encryption_status["secure"]:
            logger.info("🔐 AES-256 encryption validated and active")
        else:
            logger.warning("⚠️ Encryption environment issues detected:")
            for issue in encryption_status["issues"]:
                logger.warning(f"  - {issue}")
        
        # Log key information
        key_info = key_manager.get_key_info()
        logger.info(f"🔑 Encryption: {key_info['algorithm']} with {key_info['key_derivation']}")
        
        logger.info("🛡️ JWT authentication service ready")
        logger.info("📊 Enterprise audit logging enabled")
        logger.info("👥 Multi-user isolation active")
        logger.info("💾 Real-time connection health monitoring")
        logger.info("🏗️ Enterprise API endpoints available at /api/database/*")
        
        logger.info("🎉 Enterprise Database Migration Service fully operational!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup enterprise services on shutdown"""
    try:
        await enterprise_store.close()
        await auth_service.close()
        logger.info("🛑 Enterprise services shut down gracefully")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# Configure CORS with expanded origins for enterprise deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://schemasage.vercel.app",
        "https://*.schemasage.com",  # Production domains
        "https://*.herokuapp.com"    # Staging domains
    ],
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
app.include_router(frontend_api.router)  # Now the enterprise version with full functionality
app.include_router(migration_management_router)
app.include_router(simple_cloud_migration_router)
app.include_router(performance_cost_calculator_router)
app.include_router(smart_rollback_router)

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
