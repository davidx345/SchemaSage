from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc
from pydantic import BaseModel
from app.config import settings
from app.core.db.postgresql import get_db
from app.models.orm_models import (
    Project as ORMProject,
    SchemaStorage as ORMSchemaStorage,
)
from app.models.schemas import ProjectResponse as PydanticProjectResponse
from datetime import datetime
from typing import List, Dict, Any, Optional

router = APIRouter()


class DashboardSummaryResponse(BaseModel):
    active_projects: int
    schemas_tracked: int
    last_activity_timestamp: Optional[datetime] = None
    last_activity_description: str
    recent_projects: List[PydanticProjectResponse]


@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    try:
        active_projects_result = await db.execute(select(func.count(ORMProject.id)))
        active_projects_count = active_projects_result.scalar_one_or_none() or 0

        total_schemas_result = await db.execute(select(func.count(ORMSchemaStorage.id)))
        total_schemas_count = total_schemas_result.scalar_one_or_none() or 0

        last_activity_project_result = await db.execute(
            select(ORMProject).order_by(desc(ORMProject.updated_at)).limit(1)
        )
        last_project = last_activity_project_result.scalars().first()

        last_activity_timestamp: Optional[datetime] = None
        last_activity_description = "No recent activity"
        if last_project:
            last_activity_timestamp = last_project.updated_at
            last_activity_description = f"Updated {last_project.name}"

        recent_projects_result = await db.execute(
            select(ORMProject)
            .options(selectinload(ORMProject.schemas))
            .order_by(desc(ORMProject.updated_at))
            .limit(5)
        )
        recent_projects_orm = recent_projects_result.scalars().all()

        recent_projects_pydantic = [
            PydanticProjectResponse.from_orm(p) for p in recent_projects_orm
        ]

        return DashboardSummaryResponse(
            active_projects=active_projects_count,
            schemas_tracked=total_schemas_count,
            last_activity_timestamp=last_activity_timestamp,
            last_activity_description=last_activity_description,
            recent_projects=recent_projects_pydantic,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard summary: {str(e)}",
        )
