"""Database API endpoints for SchemaSage."""

import uuid
from fastapi import APIRouter, HTTPException, status, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ...core.db.postgresql import get_db, engine
from ...models.schemas import (
    SchemaResponse,
    ProjectCreate as PydanticProjectCreate,
    ProjectResponse as PydanticProjectResponse,
    ProjectDetailResponse as PydanticProjectDetailResponse,
    DatabaseConfig, # Added DatabaseConfig
    ProjectUpdate as PydanticProjectUpdate # Added ProjectUpdate
)
from ...models.orm_models import (
    Project as ORMProject,
    SchemaStorage as ORMSchemaStorage,
)
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/projects", response_model=List[PydanticProjectResponse])
async def get_projects(db: AsyncSession = Depends(get_db)):
    """Get all projects."""
    try:
        result = await db.execute(
            select(ORMProject)
            .options(selectinload(ORMProject.schemas))
            .order_by(ORMProject.created_at.desc())
        )
        projects = result.scalars().all()
        return projects
    except Exception as e:
        logger.exception("Error getting projects")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving projects: {str(e)}",
        )


@router.post(
    "/projects",
    response_model=PydanticProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project_data: PydanticProjectCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new project."""
    try:
        new_project = ORMProject(
            name=project_data.name, description=project_data.description
        )
        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)
        return new_project
    except Exception as e:
        logger.exception("Error creating project")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project: {str(e)}",
        )


@router.get("/projects/{project_id}", response_model=PydanticProjectDetailResponse)
async def get_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a project by ID, including its schemas."""
    try:
        result = await db.execute(
            select(ORMProject)
            .options(selectinload(ORMProject.schemas))
            .filter(ORMProject.id == project_id)
        )
        project = result.scalars().first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving project: {str(e)}",
        )


@router.put("/projects/{project_id}", response_model=PydanticProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    project_data: PydanticProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing project."""
    try:
        result = await db.execute(
            select(ORMProject).filter(ORMProject.id == project_id)
        )
        db_project = result.scalars().first()

        if not db_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )

        update_data = project_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)
        
        db_project.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_project)
        return db_project
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating project: {str(e)}",
        )


class SchemaCreateRequest(BaseModel):
    project_id: uuid.UUID
    schema_content: Dict[str, Any]  # Or your SchemaResponse model


@router.post(
    "/projects/{project_id}/schemas", response_model=PydanticProjectDetailResponse
)
async def add_schema_to_project(
    project_id: uuid.UUID,
    schema_data: SchemaResponse,
    db: AsyncSession = Depends(get_db),
):
    """Add a new schema to an existing project."""
    try:
        project_result = await db.execute(
            select(ORMProject).filter(ORMProject.id == project_id)
        )
        project = project_result.scalars().first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found. Cannot add schema.",
            )

        new_schema = ORMSchemaStorage(
            project_id=project_id, schema_data=schema_data.dict()
        )
        db.add(new_schema)
        await db.commit()
        await db.refresh(project)

        result = await db.execute(
            select(ORMProject)
            .options(selectinload(ORMProject.schemas))
            .filter(ORMProject.id == project_id)
        )
        updated_project = result.scalars().first()
        return updated_project

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error adding schema to project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding schema to project: {str(e)}",
        )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a project and its associated schemas."""
    try:
        result = await db.execute(
            select(ORMProject).filter(ORMProject.id == project_id)
        )
        project = result.scalars().first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        await db.delete(project)
        await db.commit()
        return
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting project: {str(e)}",
        )


@router.post("/connect", summary="Connect to a database (placeholder)")
async def connect_to_database(
    config: DatabaseConfig,
    # db_inspector: DatabaseInspector = Depends(DatabaseInspector) # If inspector handles connection
):
    """
    Placeholder for connecting to a database.
    Actual connection logic would be in a service.
    """
    try:
        # Example: Simulate connection test or get metadata
        # connection_successful = db_inspector.test_connection(config)
        # if not connection_successful:
        #     raise HTTPException(status_code=400, detail="Failed to connect to the database")
        # For now, just acknowledge the request
        logger.info(f"Connection request received for: {config.db_type}")
        return {"success": True, "message": "Connection request received.", "config_received": config.model_dump()}
    except Exception as e:
        logger.exception("Error in /connect endpoint")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/test", summary="Test database connection (placeholder)")
async def test_database_connection(
    config: DatabaseConfig,
    # db_inspector: DatabaseInspector = Depends(DatabaseInspector) # If inspector handles connection test
):
    """
    Tests the connection to the specified database.
    """
    try:
        # success = db_inspector.test_connection(config) # Actual test logic
        # if not success:
        #     raise HTTPException(status_code=400, detail="Database connection test failed.")
        # For now, simulate success
        logger.info(f"Test connection request for: {config.db_type}")
        return {"success": True, "message": "Database connection test successful (simulated)."}
    except Exception as e:
        logger.exception("Error testing database connection")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class DatabaseImportRequest(BaseModel):
    config: DatabaseConfig
    # tables: Optional[List[str]] = None # Or whatever structure your frontend sends for schema import
    # For now, let's assume we try to import everything the inspector can find


@router.post("/import", summary="Import database schema (placeholder)")
async def import_database_schema(
    import_request: DatabaseImportRequest, # Changed to DatabaseImportRequest
    # db_inspector: DatabaseInspector = Depends(DatabaseInspector) # If inspector handles import
):
    """
    Placeholder for importing a database schema based on connection config.
    """
    try:
        # imported_schema_data = db_inspector.import_schema(
        #     config=import_request.config,
        #     # tables=import_request.tables # if you allow specific table import
        # )
        # if not imported_schema_data:
        #     raise HTTPException(status_code=400, detail="Failed to import schema.")
        # For now, just acknowledge
        logger.info(f"Schema import request for: {import_request.config.db_type}")
        return {
            "success": True,
            "message": "Schema import request received (simulated).",
            "config_received": import_request.config.model_dump()
            # "imported_schema": imported_schema_data # if you return the schema
        }
    except Exception as e:
        logger.exception("Error during schema import")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
