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
from integrations.manager import IntegrationManager
from integrations.webhook import WebhookIntegration
from integrations.notification import NotificationIntegration
from integrations.cloud_storage import CloudStorageIntegration
from integrations.bi_tools import BIToolsIntegration
from integrations.data_catalogs import DataCatalogsIntegration
from integrations.custom_api import CustomAPIIntegration
from fastapi import Body
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Service instance
project_manager = ProjectManager()

# Integration manager instance
integration_manager = IntegrationManager()
# Register webhook integration with default config (can be updated via API)
default_webhook_config = {"enabled": False, "webhooks": [], "events": []}
integration_manager.register("webhook", WebhookIntegration, default_webhook_config)

# Register notification integration with default config
notification_default_config = {"enabled": False, "channels": [], "events": []}
integration_manager.register("notification", NotificationIntegration, notification_default_config)

# Register cloud storage integration with default config
cloud_storage_default_config = {"enabled": False, "providers": []}
integration_manager.register("cloud_storage", CloudStorageIntegration, cloud_storage_default_config)

# Register BI tools integration with default config
bi_tools_default_config = {"enabled": False, "tools": []}
integration_manager.register("bi_tools", BIToolsIntegration, bi_tools_default_config)

# Register data catalogs integration with default config
data_catalogs_default_config = {"enabled": False, "catalogs": []}
integration_manager.register("data_catalogs", DataCatalogsIntegration, data_catalogs_default_config)

# Register custom API integration with default config
custom_api_default_config = {"enabled": False, "connectors": []}
integration_manager.register("custom_api", CustomAPIIntegration, custom_api_default_config)

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

class WebhookConfigRequest(BaseModel):
    webhooks: list[str]
    events: list[str]
    enabled: bool = True

class WebhookTriggerRequest(BaseModel):
    event: str
    payload: dict

@app.get("/integrations/webhooks")
async def get_webhook_config():
    """Get current webhook integration config"""
    webhook = integration_manager.integrations.get("webhook")
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook integration not found")
    return {
        "enabled": webhook.enabled,
        "webhooks": webhook.webhooks,
        "events": webhook.events
    }

@app.post("/integrations/webhooks")
async def configure_webhook(config: WebhookConfigRequest):
    """Configure webhook integration"""
    webhook = integration_manager.integrations.get("webhook")
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook integration not found")
    integration_manager.configure("webhook", config.dict())
    return {"success": True}

@app.post("/integrations/webhooks/enable")
async def enable_webhook():
    integration_manager.enable("webhook")
    return {"success": True}

@app.post("/integrations/webhooks/disable")
async def disable_webhook():
    integration_manager.disable("webhook")
    return {"success": True}

@app.post("/integrations/webhooks/trigger")
async def trigger_webhook(req: WebhookTriggerRequest):
    webhook = integration_manager.integrations.get("webhook")
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook integration not found")
    integration_manager.trigger("webhook", req.event, req.payload)
    return {"success": True}

class NotificationConfigRequest(BaseModel):
    channels: list[dict]
    events: list[str]
    enabled: bool = True

class NotificationTriggerRequest(BaseModel):
    event: str
    payload: dict

@app.get("/integrations/notifications")
async def get_notification_config():
    """Get current notification integration config"""
    notification = integration_manager.integrations.get("notification")
    if not notification:
        raise HTTPException(status_code=404, detail="Notification integration not found")
    return {
        "enabled": notification.enabled,
        "channels": notification.channels,
        "events": notification.events
    }

@app.post("/integrations/notifications")
async def configure_notification(config: NotificationConfigRequest):
    """Configure notification integration"""
    notification = integration_manager.integrations.get("notification")
    if not notification:
        raise HTTPException(status_code=404, detail="Notification integration not found")
    integration_manager.configure("notification", config.dict())
    return {"success": True}

@app.post("/integrations/notifications/enable")
async def enable_notification():
    integration_manager.enable("notification")
    return {"success": True}

@app.post("/integrations/notifications/disable")
async def disable_notification():
    integration_manager.disable("notification")
    return {"success": True}

@app.post("/integrations/notifications/trigger")
async def trigger_notification(req: NotificationTriggerRequest):
    notification = integration_manager.integrations.get("notification")
    if not notification:
        raise HTTPException(status_code=404, detail="Notification integration not found")
    integration_manager.trigger("notification", req.event, req.payload)
    return {"success": True}

class CloudStorageConfigRequest(BaseModel):
    providers: list[dict]
    enabled: bool = True

class CloudStorageTriggerRequest(BaseModel):
    event: str
    payload: dict

@app.get("/integrations/cloud-storage")
async def get_cloud_storage_config():
    """Get current cloud storage integration config"""
    cloud_storage = integration_manager.integrations.get("cloud_storage")
    if not cloud_storage:
        raise HTTPException(status_code=404, detail="Cloud storage integration not found")
    return {
        "enabled": cloud_storage.enabled,
        "providers": cloud_storage.providers
    }

@app.post("/integrations/cloud-storage")
async def configure_cloud_storage(config: CloudStorageConfigRequest):
    """Configure cloud storage integration"""
    cloud_storage = integration_manager.integrations.get("cloud_storage")
    if not cloud_storage:
        raise HTTPException(status_code=404, detail="Cloud storage integration not found")
    integration_manager.configure("cloud_storage", config.dict())
    return {"success": True}

@app.post("/integrations/cloud-storage/enable")
async def enable_cloud_storage():
    integration_manager.enable("cloud_storage")
    return {"success": True}

@app.post("/integrations/cloud-storage/disable")
async def disable_cloud_storage():
    integration_manager.disable("cloud_storage")
    return {"success": True}

@app.post("/integrations/cloud-storage/trigger")
async def trigger_cloud_storage(req: CloudStorageTriggerRequest):
    cloud_storage = integration_manager.integrations.get("cloud_storage")
    if not cloud_storage:
        raise HTTPException(status_code=404, detail="Cloud storage integration not found")
    integration_manager.trigger("cloud_storage", req.event, req.payload)
    return {"success": True}

class BIToolsConfigRequest(BaseModel):
    tools: list[dict]
    enabled: bool = True

class BIToolsTriggerRequest(BaseModel):
    event: str
    payload: dict

@app.get("/integrations/bi-tools")
async def get_bi_tools_config():
    """Get current BI tools integration config"""
    bi_tools = integration_manager.integrations.get("bi_tools")
    if not bi_tools:
        raise HTTPException(status_code=404, detail="BI tools integration not found")
    return {
        "enabled": bi_tools.enabled,
        "tools": bi_tools.tools
    }

@app.post("/integrations/bi-tools")
async def configure_bi_tools(config: BIToolsConfigRequest):
    """Configure BI tools integration"""
    bi_tools = integration_manager.integrations.get("bi_tools")
    if not bi_tools:
        raise HTTPException(status_code=404, detail="BI tools integration not found")
    integration_manager.configure("bi_tools", config.dict())
    return {"success": True}

@app.post("/integrations/bi-tools/enable")
async def enable_bi_tools():
    integration_manager.enable("bi_tools")
    return {"success": True}

@app.post("/integrations/bi-tools/disable")
async def disable_bi_tools():
    integration_manager.disable("bi_tools")
    return {"success": True}

@app.post("/integrations/bi-tools/trigger")
async def trigger_bi_tools(req: BIToolsTriggerRequest):
    bi_tools = integration_manager.integrations.get("bi_tools")
    if not bi_tools:
        raise HTTPException(status_code=404, detail="BI tools integration not found")
    integration_manager.trigger("bi_tools", req.event, req.payload)
    return {"success": True}

class DataCatalogsConfigRequest(BaseModel):
    catalogs: list[dict]
    enabled: bool = True

class DataCatalogsTriggerRequest(BaseModel):
    event: str
    payload: dict

@app.get("/integrations/data-catalogs")
async def get_data_catalogs_config():
    """Get current data catalogs integration config"""
    data_catalogs = integration_manager.integrations.get("data_catalogs")
    if not data_catalogs:
        raise HTTPException(status_code=404, detail="Data catalogs integration not found")
    return {
        "enabled": data_catalogs.enabled,
        "catalogs": data_catalogs.catalogs
    }

@app.post("/integrations/data-catalogs")
async def configure_data_catalogs(config: DataCatalogsConfigRequest):
    """Configure data catalogs integration"""
    data_catalogs = integration_manager.integrations.get("data_catalogs")
    if not data_catalogs:
        raise HTTPException(status_code=404, detail="Data catalogs integration not found")
    integration_manager.configure("data_catalogs", config.dict())
    return {"success": True}

@app.post("/integrations/data-catalogs/enable")
async def enable_data_catalogs():
    integration_manager.enable("data_catalogs")
    return {"success": True}

@app.post("/integrations/data-catalogs/disable")
async def disable_data_catalogs():
    integration_manager.disable("data_catalogs")
    return {"success": True}

@app.post("/integrations/data-catalogs/trigger")
async def trigger_data_catalogs(req: DataCatalogsTriggerRequest):
    data_catalogs = integration_manager.integrations.get("data_catalogs")
    if not data_catalogs:
        raise HTTPException(status_code=404, detail="Data catalogs integration not found")
    integration_manager.trigger("data_catalogs", req.event, req.payload)
    return {"success": True}

class CustomAPIConfigRequest(BaseModel):
    connectors: list[dict]
    enabled: bool = True

class CustomAPITriggerRequest(BaseModel):
    event: str
    payload: dict

@app.get("/integrations/custom-api")
async def get_custom_api_config():
    """Get current custom API integration config"""
    custom_api = integration_manager.integrations.get("custom_api")
    if not custom_api:
        raise HTTPException(status_code=404, detail="Custom API integration not found")
    return {
        "enabled": custom_api.enabled,
        "connectors": custom_api.connectors
    }

@app.post("/integrations/custom-api")
async def configure_custom_api(config: CustomAPIConfigRequest):
    """Configure custom API integration"""
    custom_api = integration_manager.integrations.get("custom_api")
    if not custom_api:
        raise HTTPException(status_code=404, detail="Custom API integration not found")
    integration_manager.configure("custom_api", config.dict())
    return {"success": True}

@app.post("/integrations/custom-api/enable")
async def enable_custom_api():
    integration_manager.enable("custom_api")
    return {"success": True}

@app.post("/integrations/custom-api/disable")
async def disable_custom_api():
    integration_manager.disable("custom_api")
    return {"success": True}

@app.post("/integrations/custom-api/trigger")
async def trigger_custom_api(req: CustomAPITriggerRequest):
    custom_api = integration_manager.integrations.get("custom_api")
    if not custom_api:
        raise HTTPException(status_code=404, detail="Custom API integration not found")
    integration_manager.trigger("custom_api", req.event, req.payload)
    return {"success": True}

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
            "enable_webhook": "POST /integrations/webhooks/enable",
            "disable_webhook": "POST /integrations/webhooks/disable",
            "trigger_webhook": "POST /integrations/webhooks/trigger",
            "notification_config": "GET /integrations/notifications",
            "configure_notification": "POST /integrations/notifications",
            "enable_notification": "POST /integrations/notifications/enable",
            "disable_notification": "POST /integrations/notifications/disable",
            "trigger_notification": "POST /integrations/notifications/trigger",
            "cloud_storage_config": "GET /integrations/cloud-storage",
            "configure_cloud_storage": "POST /integrations/cloud-storage",
            "enable_cloud_storage": "POST /integrations/cloud-storage/enable",
            "disable_cloud_storage": "POST /integrations/cloud-storage/disable",
            "trigger_cloud_storage": "POST /integrations/cloud-storage/trigger",
            "bi_tools_config": "GET /integrations/bi-tools",
            "configure_bi_tools": "POST /integrations/bi-tools",
            "enable_bi_tools": "POST /integrations/bi-tools/enable",
            "disable_bi_tools": "POST /integrations/bi-tools/disable",
            "trigger_bi_tools": "POST /integrations/bi-tools/trigger",
            "data_catalogs_config": "GET /integrations/data-catalogs",
            "configure_data_catalogs": "POST /integrations/data-catalogs",
            "enable_data_catalogs": "POST /integrations/data-catalogs/enable",
            "disable_data_catalogs": "POST /integrations/data-catalogs/disable",
            "trigger_data_catalogs": "POST /integrations/data-catalogs/trigger",
            "custom_api_config": "GET /integrations/custom-api",
            "configure_custom_api": "POST /integrations/custom-api",
            "enable_custom_api": "POST /integrations/custom-api/enable",
            "disable_custom_api": "POST /integrations/custom-api/disable",
            "trigger_custom_api": "POST /integrations/custom-api/trigger"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
