"""
Project Management Microservice
Handles project creation, management, and tracking
"""
from fastapi import FastAPI, HTTPException, Request, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional
import logging
from contextlib import asynccontextmanager

from config import settings
from models.schemas import (
    Project, ProjectStatus, ProjectType, CreateProjectRequest, UpdateProjectRequest,
    ApiHealthResponse, ProjectListResponse,  # <-- add these
    GlossaryTerm, GlossaryRequest, GlossaryResponse,
    SchemaConsistencyCheckRequest, SchemaConsistencyCheckResponse
)
from core.project_manager import ProjectManager, ProjectError

logger = logging.getLogger(__name__)

# Service instance
project_manager = ProjectManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Project Management Service starting up...")
    logger.info(f"Storage directory: {settings.UPLOAD_DIR}")
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
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Handle project management errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": str(exc),
            "status": "error",
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Error in Project Management Service: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "details": {"error": str(exc)},
        },
    )

@app.get("/health", response_model=ApiHealthResponse)
async def health_check():
    """Health check endpoint"""
    project_count = await project_manager.get_project_count()
    
    return ApiHealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        project_count=project_count
    )

@app.post("/projects", response_model=Project)
async def create_project(request: CreateProjectRequest):
    """Create a new project"""
    try:
        project = await project_manager.create_project(request)
        return project
    except ProjectError as e:
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    type: Optional[ProjectType] = Query(None, description="Filter by type")
):
    """List projects with pagination and filtering"""
    try:
        projects, total = await project_manager.list_projects(
            page=page, size=size, status=status, type=type
        )
        
        return ProjectListResponse(
            projects=projects,
            total=total,
            page=page,
            size=size
        )
    except ProjectError as e:
        logger.error(f"Failed to list projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a specific project"""
    try:
        project = await project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except ProjectError as e:
        logger.error(f"Failed to get project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, request: UpdateProjectRequest):
    """Update a project"""
    try:
        project = await project_manager.update_project(project_id, request)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except ProjectError as e:
        logger.error(f"Failed to update project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        deleted = await project_manager.delete_project(project_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except ProjectError as e:
        logger.error(f"Failed to delete project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/search/{query}")
async def search_projects(query: str):
    """Search projects by name or description"""
    try:
        projects = await project_manager.search_projects(query)
        return {"projects": projects, "count": len(projects)}
    except ProjectError as e:
        logger.error(f"Failed to search projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_project_stats():
    """Get project statistics"""
    try:
        # This could be expanded with more detailed analytics
        projects, total = await project_manager.list_projects(page=1, size=1000)
        
        stats = {
            "total_projects": total,
            "by_status": {},
            "by_type": {}
        }
        
        for project in projects:
            # Count by status
            status_key = project.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
            
            # Count by type
            type_key = project.type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
        
        return stats
    except ProjectError as e:
        logger.error(f"Failed to get project stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/glossary", response_model=GlossaryResponse)
async def list_glossary_terms():
    """List all glossary terms"""
    terms = await project_manager.list_glossary_terms()
    return GlossaryResponse(terms=terms, total=len(terms))

@app.post("/glossary", response_model=GlossaryTerm)
async def add_glossary_term(request: GlossaryRequest):
    """Add a new glossary term"""
    term = await project_manager.add_glossary_term(request)
    return term

@app.put("/glossary/{term_id}", response_model=GlossaryTerm)
async def update_glossary_term(term_id: str, request: GlossaryRequest):
    """Update an existing glossary term"""
    term = await project_manager.update_glossary_term(term_id, request)
    return term

@app.delete("/glossary/{term_id}")
async def delete_glossary_term(term_id: str):
    """Delete a glossary term"""
    await project_manager.delete_glossary_term(term_id)
    return {"success": True}

@app.post("/schema/consistency-check", response_model=SchemaConsistencyCheckResponse)
async def schema_consistency_check(request: SchemaConsistencyCheckRequest):
    """Check schema consistency"""
    result = await project_manager.schema_consistency_check(request)
    return result

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
            "schema_consistency_check": "POST /schema/consistency-check"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
