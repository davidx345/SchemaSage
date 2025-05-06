"""Database API endpoints for SchemaSage."""
from fastapi import APIRouter, HTTPException, status, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from ...core.db import db
from ...models.schemas import SchemaResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionConfig(BaseModel):
    """Database connection configuration."""
    type: str = "mongodb"
    host: Optional[str] = "localhost"
    port: Optional[int] = 27017
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None

class TestConnectionResponse(BaseModel):
    """Response for test connection endpoint."""
    success: bool
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class DatabaseImportResponse(BaseModel):
    """Response for database import endpoint."""
    schema: SchemaResponse
    metadata: Optional[Dict[str, Any]] = None
    tables_imported: int

class CreateProjectRequest(BaseModel):
    """Request to create a new project."""
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    """Project data response."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str

class ProjectListResponse(BaseModel):
    """List of projects response."""
    projects: List[ProjectResponse]
    total: int

@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(config: ConnectionConfig):
    """Test connection to a database."""
    try:
        if config.type != "mongodb":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"Database type '{config.type}' is not yet supported. Currently only MongoDB is supported.",
                    "details": {"supported_types": ["mongodb"]}
                }
            )

        connection_success = await db.test_connection()

        if connection_success:
            db_info = await db.get_database_info()
            return {
                "success": True,
                "message": "Successfully connected to MongoDB",
                "details": db_info
            }
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "success": False,
                    "message": "Failed to connect to MongoDB. Make sure MongoDB is running and accessible.",
                }
            )
    except Exception as e:
        logger.exception("Error testing database connection")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Error testing connection: {str(e)}"
            }
        )

@router.post("/import", response_model=DatabaseImportResponse)
async def import_from_database(config: ConnectionConfig):
    """Import schema from a database."""
    try:
        if config.type != "mongodb":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database type '{config.type}' is not yet supported. Currently only MongoDB is supported."
            )

        # For now, we'll return a sample schema since we're not actually connecting to external DBs
        # In a real implementation, you would extract the schema from the specified database
        from ...core.schema_detector import SchemaDetector
        detector = SchemaDetector()
        
        # Sample JSON for a basic schema
        sample_json = """
        {
            "users": [
                {"id": 1, "username": "john_doe", "email": "john@example.com", "age": 30},
                {"id": 2, "username": "jane_doe", "email": "jane@example.com", "age": 25}
            ],
            "posts": [
                {"id": 101, "user_id": 1, "title": "First post", "content": "This is my first post"},
                {"id": 102, "user_id": 2, "title": "Hello world", "content": "Hello from Jane"}
            ]
        }
        """
        
        schema = await detector.detect_from_text(sample_json)
        
        return {
            "schema": schema,
            "metadata": {
                "source": f"Import from {config.type}",
                "database": config.database
            },
            "tables_imported": len(schema.tables)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error importing from database")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing schema: {str(e)}"
        )

@router.post("/connect", response_model=DatabaseImportResponse)
async def connect_to_database(config: ConnectionConfig):
    """Connect to a database and retrieve its schema."""
    # This endpoint is an alias for /import for now
    return await import_from_database(config)

# Project management endpoints
@router.get("/projects", response_model=ProjectListResponse)
async def get_projects():
    """Get all projects."""
    try:
        projects = await db.get_projects()
        return {
            "projects": projects,
            "total": len(projects)
        }
    except Exception as e:
        logger.exception("Error getting projects")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving projects: {str(e)}"
        )

@router.post("/projects", response_model=ProjectResponse)
async def create_project(project_data: CreateProjectRequest):
    """Create a new project."""
    try:
        project = await db.create_project(
            name=project_data.name,
            description=project_data.description
        )
        return project
    except Exception as e:
        logger.exception("Error creating project")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project: {str(e)}"
        )

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a project by ID."""
    try:
        project = await db.get_project(project_id)
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error getting project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting project: {str(e)}"
        )

@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_data: dict = Body(...)):
    """Update a project."""
    try:
        project = await db.update_project(project_id, project_data)
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error updating project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating project: {str(e)}"
        )

@router.delete("/projects/{project_id}", response_model=dict)
async def delete_project(project_id: str):
    """Delete a project."""
    try:
        success = await db.delete_project(project_id)
        if success:
            return {"success": True, "message": f"Project {project_id} deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
    except Exception as e:
        logger.exception(f"Error deleting project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting project: {str(e)}"
        )

@router.get("/projects/{project_id}/schema", response_model=SchemaResponse)
async def get_project_schema(project_id: str):
    """Get the schema for a project."""
    try:
        schema = await db.get_schema(project_id)
        return schema
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error getting schema for project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving schema: {str(e)}"
        )

@router.post("/projects/{project_id}/schema", response_model=dict)
async def save_project_schema(project_id: str, schema: SchemaResponse):
    """Save a schema for a project."""
    try:
        result = await db.save_schema(project_id, schema)
        return {
            "success": True,
            "message": f"Schema saved for project {project_id}",
            "schema_id": result.get("_id", project_id)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error saving schema for project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving schema: {str(e)}"
        )