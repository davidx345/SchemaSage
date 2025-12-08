from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from core.database_service import ProjectManagementDatabaseService
from core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# ===== REQUEST/RESPONSE MODELS =====

class DashboardStats(BaseModel):
    """Dashboard statistics response model."""
    schemas_created: int
    code_generated: int
    quick_deploys: int
    migrations_run: int
    etl_pipelines: int
    compliance_checks: int
    db_connections: int
    api_calls: int

class ActivityItem(BaseModel):
    """Single activity item."""
    id: str
    type: str
    message: str
    timestamp: str
    user: str
    status: str

class DashboardActivities(BaseModel):
    """Dashboard activities response model."""
    recentActivities: List[ActivityItem]

# ===== ENDPOINTS =====

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(ProjectManagementDatabaseService.get_db)
):
    """
    Get dashboard statistics.
    
    Returns counts for:
    - schemas_created: Number of schemas created
    - code_generated: Number of code generation requests
    - quick_deploys: Number of cloud deployments
    - migrations_run: Number of database migrations
    - etl_pipelines: Number of ETL pipelines created
    - compliance_checks: Number of compliance scans
    - db_connections: Number of database connections
    - api_calls: Total API calls made
    """
    try:
        user_id = current_user.get("user_id")
        logger.info(f"📊 Fetching dashboard stats for user {user_id}")
        
        # TODO: Query actual database tables for real counts
        # For now, return mock data
        stats = DashboardStats(
            schemas_created=0,
            code_generated=0,
            quick_deploys=0,
            migrations_run=0,
            etl_pipelines=0,
            compliance_checks=0,
            db_connections=0,
            api_calls=0
        )
        
        # Query each metric (when tables are available):
        # stats.schemas_created = db.query(Schema).filter_by(user_id=user_id).count()
        # stats.code_generated = db.query(CodeGeneration).filter_by(user_id=user_id).count()
        # stats.quick_deploys = db.query(Deployment).filter_by(user_id=user_id).count()
        # stats.migrations_run = db.query(Migration).filter_by(user_id=user_id).count()
        # stats.etl_pipelines = db.query(ETLPipeline).filter_by(user_id=user_id).count()
        # stats.compliance_checks = db.query(ComplianceScan).filter_by(user_id=user_id).count()
        # stats.db_connections = db.query(DatabaseConnection).filter_by(user_id=user_id).count()
        # stats.api_calls = db.query(APICall).filter_by(user_id=user_id).count()
        
        logger.info(f"✅ Dashboard stats retrieved successfully")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error fetching dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard statistics: {str(e)}"
        )

@router.get("/activities", response_model=DashboardActivities)
async def get_dashboard_activities(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(ProjectManagementDatabaseService.get_db)
):
    """
    Get recent dashboard activities.
    
    Returns list of recent user activities including:
    - Schema creations
    - Code generations
    - Cloud deployments
    - Database migrations
    - ETL pipeline runs
    - Compliance checks
    
    Query parameters:
    - limit: Maximum number of activities to return (default: 10)
    """
    try:
        user_id = current_user.get("user_id")
        username = current_user.get("username", "Unknown")
        logger.info(f"📋 Fetching dashboard activities for user {user_id}, limit={limit}")
        
        # TODO: Query actual activity log table
        # For now, return mock data
        activities = []
        
        # Example query (when ActivityLog table exists):
        # activities_raw = db.query(ActivityLog)\
        #     .filter_by(user_id=user_id)\
        #     .order_by(ActivityLog.timestamp.desc())\
        #     .limit(limit)\
        #     .all()
        # 
        # activities = [
        #     ActivityItem(
        #         id=str(activity.id),
        #         type=activity.type,
        #         message=activity.message,
        #         timestamp=activity.timestamp.isoformat() + "Z",
        #         user=username,
        #         status=activity.status
        #     )
        #     for activity in activities_raw
        # ]
        
        logger.info(f"✅ Retrieved {len(activities)} dashboard activities")
        return DashboardActivities(recentActivities=activities)
        
    except Exception as e:
        logger.error(f"❌ Error fetching dashboard activities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard activities: {str(e)}"
        )
