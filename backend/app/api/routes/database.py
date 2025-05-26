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
