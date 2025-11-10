"""
Project Management Microservice
Handles project management, and tracking
"""
from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import uuid4

from config import settings
from models.schemas import ApiHealthResponse
from models.database_models import Project, ProjectFile, ProjectSchema, ProjectActivity
from core.database_service import ProjectManagementDatabaseService
from core.auth import get_current_user, get_optional_user
from core.project_manager import ProjectError
from routers import (
    projects_router, stats_router, integrations_router, 
    glossary_router, team_router, websocket_router, upload_router,
    compliance_router
)

logger = logging.getLogger(__name__)

# Database service
db_service = ProjectManagementDatabaseService()


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
    
    # Initialize database
    try:
        await db_service.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    yield
    
    # Shutdown
    logger.info("Project Management Service shutting down...")
    try:
        await db_service.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


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

# Include all routers
app.include_router(projects_router)
app.include_router(stats_router)
app.include_router(integrations_router)
app.include_router(glossary_router)
app.include_router(team_router)
app.include_router(websocket_router)
app.include_router(upload_router)
app.include_router(compliance_router)

# Import and include new routers
from routers.comments import router as comments_router
from routers.collaboration import router as collaboration_router
from routers.data_dictionary_integration import router as data_dict_router
from routers.marketplace import router as marketplace_router
from routers.compliance_alerts import router as compliance_alerts_router
from routers.regulatory_notifications import router as regulatory_notifications_router
from routers.multi_tenant import router as multi_tenant_router
from routers.payment_analytics import router as payment_analytics_router
from routers.activity_tracking import router as activity_tracking_router

app.include_router(comments_router)
app.include_router(collaboration_router)
app.include_router(data_dict_router)
app.include_router(marketplace_router)
app.include_router(compliance_alerts_router)
app.include_router(regulatory_notifications_router)
app.include_router(multi_tenant_router)
app.include_router(payment_analytics_router)
app.include_router(activity_tracking_router)

# Premium Features
from routers.experiments import router as experiments_router
from routers.data_valuation import router as data_valuation_router
from routers.data_marketplace import router as data_marketplace_router

app.include_router(experiments_router)
app.include_router(data_valuation_router)
app.include_router(data_marketplace_router)


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


@app.get("/stats")
async def get_service_stats(
    current_user: str = Depends(get_optional_user)
):
    """
    Get project management service statistics for authenticated user
    
    ✅ FIXED: Now filters by user_id to ensure data isolation
    """
    try:
        # Get real stats from database filtered by user
        from sqlalchemy import func, select
        from datetime import timedelta
        
        async with db_service.get_session() as session:
            # Total projects for this user
            total_projects = await session.scalar(
                select(func.count(Project.id))
                .where(Project.user_id == current_user)
                .execution_options(prepared_statement_cache_size=0)
            ) or 0
            
            # Active projects (status = 'active')
            active_projects = await session.scalar(
                select(func.count(Project.id))
                .where(Project.user_id == current_user)
                .where(Project.status == 'active')
                .execution_options(prepared_statement_cache_size=0)
            ) or 0
            
            # Projects created today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            projects_today = await session.scalar(
                select(func.count(Project.id))
                .where(Project.user_id == current_user)
                .where(Project.created_at >= today_start)
                .execution_options(prepared_statement_cache_size=0)
            ) or 0
            
            stats = {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "projects_today": projects_today,
                "total_collaborations": 0,  # Can be enhanced with actual collaboration count
                "active_collaborations": 0,
                "marketplace_transactions": 0,  # Can be enhanced with actual transaction count
                "compliance_checks": 0,  # Can be enhanced with actual compliance count
                "team_members": 1,  # Current user
                "service_status": "healthy",
                "database_enabled": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Project management stats for user {current_user}: {stats}")
            return stats
        
    except Exception as e:
        logger.error(f"Error getting project management stats: {e}")
        # Return safe defaults even on error
        return {
            "total_projects": 0,
            "active_projects": 0,
            "projects_today": 0,
            "total_collaborations": 0,
            "active_collaborations": 0,
            "marketplace_transactions": 0,
            "compliance_checks": 0,
            "team_members": 0,
            "service_status": "error",
            "database_enabled": False,
            "timestamp": datetime.now().isoformat()
        }


# Database-backed project endpoints
@app.post("/api/projects")
async def create_project_db(
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Create a new project in database"""
    try:
        # Extract data from request
        name = request.get("name")
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project name is required"
            )
        
        # Create project with named arguments
        project_id = await db_service.create_project(
            user_id=user_id,
            name=name,
            description=request.get("description", ""),
            project_type=request.get("project_type", "database_migration"),
            settings=request.get("metadata", {}),
            tags=request.get("tags", [])
        )
        
        return {
            "status": "success",
            "project_id": project_id,
            "message": "Project created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@app.get("/api/projects")
async def get_user_projects_db(
    user_id: str = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    status_filter: str = None
):
    """Get user's projects from database"""
    try:
        projects = await db_service.get_user_projects(user_id, limit, offset, status_filter)
        
        # The service already returns a list of dictionaries
        return {
            "status": "success",
            "projects": projects
        }
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch projects"
        )


@app.get("/api/projects/{project_id}")
async def get_project_db(
    project_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get specific project from database"""
    try:
        project = await db_service.get_project_details(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return {
            "status": "success",
            "project": project
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project"
        )


@app.put("/api/projects/{project_id}")
async def update_project_db(
    project_id: str,
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Update project in database"""
    try:
        updated_project = await db_service.update_project(project_id, user_id, request)
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return {
            "status": "success",
            "message": "Project updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@app.post("/api/projects/{project_id}/files")
async def add_project_file_db(
    project_id: str,
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Add file to project in database"""
    try:
        file_data = {
            "file_id": str(uuid4()),
            "project_id": project_id,
            "user_id": user_id,
            "filename": request.get("filename"),
            "file_type": request.get("file_type"),
            "file_size": request.get("file_size", 0),
            "file_path": request.get("file_path"),
            "metadata": request.get("metadata", {})
        }
        
        file_record = await db_service.add_project_file(file_data)
        return {
            "status": "success",
            "file_id": file_record.file_id,
            "message": "File added to project successfully"
        }
    except Exception as e:
        logger.error(f"Error adding project file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add file to project"
        )


@app.post("/api/projects/{project_id}/activity")
async def log_project_activity_db(
    project_id: str,
    request: dict,
    user_id: str = Depends(get_current_user)
):
    """Log project activity in database"""
    try:
        activity_data = {
            "activity_id": str(uuid4()),
            "project_id": project_id,
            "user_id": user_id,
            "activity_type": request.get("activity_type"),
            "description": request.get("description"),
            "metadata": request.get("metadata", {})
        }
        
        activity = await db_service.log_project_activity(activity_data)
        return {
            "status": "success",
            "activity_id": activity.activity_id,
            "message": "Activity logged successfully"
        }
    except Exception as e:
        logger.error(f"Error logging project activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log project activity"
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
