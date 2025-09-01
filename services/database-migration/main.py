"""
Database Migration Service Main Application - Modularized
Enterprise-grade database migration platform with comprehensive features
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import only the basic router for now (simplified version)
from routers import basic

# Configure logging
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

# Include only basic router for now (simplified deployment)
app.include_router(basic.router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
