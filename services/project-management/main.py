"""
Project Management Microservice
Handles project creation, management, and tracking
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from contextlib import asynccontextmanager

from config import settings
from models.schemas import ApiHealthResponse
from core.project_manager import ProjectError
from routers import (
    projects_router, stats_router, integrations_router, 
    glossary_router, team_router, websocket_router, upload_router
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Project Management Service starting up...")
    if settings.USE_S3:
        logger.info(f"Using S3 storage: {settings.S3_BUCKET_NAME}")
    else:
        logger.info(f"Using local storage: {settings.UPLOAD_DIR}")
    logger.info(f"Max file size: {settings.MAX_FILE_SIZE} bytes")
    yield
    # Shutdown
    logger.info("Project Management Service shutting down...")


app = FastAPI(
    title="Project Management Service",
    description="Microservice for managing SchemaSage projects",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://schemasage.vercel.app"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects_router)
app.include_router(stats_router)
app.include_router(integrations_router)
app.include_router(glossary_router)
app.include_router(team_router)
app.include_router(websocket_router)
app.include_router(upload_router)


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Invalid request format",
            "details": exc.errors(),
            "status": "error",
        },
    )


@app.exception_handler(ProjectError)
async def project_exception_handler(request: Request, exc: ProjectError):
    """Handle project-specific errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": str(exc), "status": "error"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "status": "error"},
    )


@app.get("/health", response_model=ApiHealthResponse)
async def health_check():
    """Health check endpoint"""
    return ApiHealthResponse(
        status="healthy",
        service="project-management",
        version=settings.SERVICE_VERSION,
        timestamp=None
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Project Management Service",
        "status": "running",
        "version": settings.SERVICE_VERSION,
        "endpoints": {
            "create_project": "POST /projects",
            "list_projects": "GET /projects",
            "get_project": "GET /projects/{project_id}",
            "update_project": "PUT /projects/{project_id}",
            "delete_project": "DELETE /projects/{project_id}",
            "search_projects": "GET /projects/search/{query}",
            "project_stats": "GET /stats",
            "health": "GET /health",
            "list_glossary_terms": "GET /glossary",
            "add_glossary_term": "POST /glossary",
            "update_glossary_term": "PUT /glossary/{term_id}",
            "delete_glossary_term": "DELETE /glossary/{term_id}",
            "schema_consistency_check": "POST /schema/consistency-check",
            "webhook_config": "GET /integrations/webhooks",
            "configure_webhook": "POST /integrations/webhooks",
            "notification_config": "GET /integrations/notifications",
            "configure_notification": "POST /integrations/notifications",
            "cloud_storage_config": "GET /integrations/cloud-storage",
            "configure_cloud_storage": "POST /integrations/cloud-storage",
            "bi_tools_config": "GET /integrations/bi-tools",
            "configure_bi_tools": "POST /integrations/bi-tools",
            "data_catalogs_config": "GET /integrations/data-catalogs",
            "configure_data_catalogs": "POST /integrations/data-catalogs",
            "custom_api_config": "GET /integrations/custom-api",
            "configure_custom_api": "POST /integrations/custom-api",
            "websocket_schema_edit": "WS /ws/schema-edit/{project_id}",
            "add_comment": "POST /projects/{project_id}/comments",
            "get_comments": "GET /projects/{project_id}/comments",
            "delete_comment": "DELETE /projects/{project_id}/comments/{comment_idx}",
            "create_team": "POST /teams",
            "get_team": "GET /teams/{team_id}",
            "invite_to_team": "POST /teams/{team_id}/invite",
            "set_team_role": "POST /teams/{team_id}/role"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
