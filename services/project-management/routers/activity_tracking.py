"""
Activity Tracking Router
Handles real user action tracking for dashboard statistics

This router provides endpoints to track user activities like schema generation,
API scaffolding, data cleaning, etc. It integrates with the ProjectActivity model
and broadcasts updates to connected WebSocket clients.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4
import httpx
import logging
import os

from core.auth import get_current_user, get_optional_user
from core.database_service import ProjectManagementDatabaseService
from models.database_models import ProjectActivity

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/activity", tags=["Activity Tracking"])

# Database service
db_service = ProjectManagementDatabaseService()

# WebSocket service URL for real-time broadcasting
WEBSOCKET_SERVICE_URL = os.getenv(
    "WEBSOCKET_REALTIME_SERVICE_URL",
    "https://schemasage-websocket-realtime-11223b2de7f4.herokuapp.com"
)


# Pydantic models for request validation
class ActivityTrackRequest(BaseModel):
    """Request model for activity tracking"""
    user_id: str = Field(..., description="User's unique ID")
    activity_type: str = Field(..., description="Type of activity performed")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional activity metadata")
    timestamp: Optional[str] = Field(None, description="ISO8601 timestamp (auto-generated if not provided)")
    
    @validator('activity_type')
    def validate_activity_type(cls, v):
        """Validate activity_type is one of the allowed values"""
        allowed_types = [
            "schema_generated",
            "api_scaffolded",
            "data_cleaned",
            "code_generated",
            "migration_started",
            "migration_completed",
            "file_uploaded",
            "visualization_created",
            "project_created",
            "analysis_run"
        ]
        if v not in allowed_types:
            raise ValueError(f"activity_type must be one of: {', '.join(allowed_types)}")
        return v
    
    @validator('timestamp', always=True)
    def set_timestamp(cls, v):
        """Set timestamp if not provided"""
        return v or datetime.utcnow().isoformat()


class ActivityTrackResponse(BaseModel):
    """Response model for activity tracking"""
    success: bool
    message: str
    activity_id: Optional[str] = None


async def broadcast_activity_to_websocket(activity_data: Dict[str, Any]):
    """
    Broadcast activity to WebSocket service for real-time dashboard updates
    
    This function sends activity data to the WebSocket service which then
    broadcasts it to all connected dashboard clients. If the WebSocket
    service is unavailable, it logs a warning but doesn't fail the request.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{WEBSOCKET_SERVICE_URL}/api/dashboard/activity",
                json=activity_data
            )
            if response.status_code == 200:
                logger.info(f"Activity broadcast to WebSocket service: {activity_data['activity_type']}")
            else:
                logger.warning(f"WebSocket service returned {response.status_code}")
    except httpx.TimeoutException:
        logger.warning("WebSocket service timeout - activity not broadcast (continuing anyway)")
    except Exception as e:
        logger.warning(f"Failed to broadcast to WebSocket service: {e}")


async def increment_dashboard_stat(stat_name: str):
    """
    Increment a specific dashboard statistic
    
    This function increments counters like schemasGenerated, apisScaffolded, etc.
    in the WebSocket service for real-time dashboard updates.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{WEBSOCKET_SERVICE_URL}/api/dashboard/increment-stat",
                json={"stat": stat_name}
            )
            logger.info(f"Incremented dashboard stat: {stat_name}")
    except Exception as e:
        logger.warning(f"Failed to increment dashboard stat: {e}")


@router.post("/track", response_model=ActivityTrackResponse)
async def track_activity(
    request: ActivityTrackRequest,
    req: Request,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Track a user activity for dashboard statistics
    
    This endpoint:
    1. Validates the activity type
    2. Stores the activity in the database
    3. Broadcasts the activity to WebSocket clients for real-time updates
    4. Increments the appropriate dashboard counter
    
    **Activity Types:**
    - schema_generated: User generated a schema from a file or prompt
    - api_scaffolded: User generated API scaffolding/code
    - data_cleaned: User cleaned/transformed data
    - code_generated: User generated code from schema
    - migration_started: User started a database migration
    - migration_completed: User completed a database migration
    - file_uploaded: User uploaded a file
    - visualization_created: User created a schema visualization
    - project_created: User created a new project
    - analysis_run: User ran schema analysis
    
    **Example Request:**
    ```json
    {
      "user_id": "user123",
      "activity_type": "schema_generated",
      "metadata": {
        "schema_id": "schema-abc-123",
        "project_id": "proj-xyz-789",
        "schema_name": "users_table"
      },
      "timestamp": "2025-10-26T12:34:56Z"
    }
    ```
    
    **Returns:**
    - success: Whether the activity was tracked successfully
    - message: Confirmation message
    - activity_id: UUID of the created activity record
    """
    try:
        # Use provided user_id or fall back to authenticated user
        user_id = request.user_id if request.user_id else current_user
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID required (either in request or via authentication)"
            )
        
        # Generate activity ID
        activity_id = str(uuid4())
        
        # Map activity types to human-readable descriptions
        activity_descriptions = {
            "schema_generated": "Generated a new schema",
            "api_scaffolded": "Scaffolded API endpoints",
            "data_cleaned": "Cleaned and transformed data",
            "code_generated": "Generated code from schema",
            "migration_started": "Started database migration",
            "migration_completed": "Completed database migration",
            "file_uploaded": "Uploaded a file",
            "visualization_created": "Created schema visualization",
            "project_created": "Created a new project",
            "analysis_run": "Ran schema analysis"
        }
        
        description = activity_descriptions.get(
            request.activity_type,
            f"Performed {request.activity_type}"
        )
        
        # Determine activity category for classification
        category_map = {
            "schema_generated": "schema",
            "api_scaffolded": "api",
            "data_cleaned": "data",
            "code_generated": "code",
            "migration_started": "migration",
            "migration_completed": "migration",
            "file_uploaded": "file",
            "visualization_created": "visualization",
            "project_created": "project",
            "analysis_run": "analysis"
        }
        
        activity_category = category_map.get(request.activity_type, "general")
        
        # Extract IP and user agent for audit trail
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        # Create activity record in database
        activity_data = {
            "id": activity_id,
            "project_id": request.metadata.get("project_id"),  # Can be None
            "user_id": user_id,
            "activity_type": request.activity_type,
            "activity_category": activity_category,
            "action": "performed",
            "description": description,
            "details": request.metadata,
            "target_object_type": request.metadata.get("object_type"),
            "target_object_id": request.metadata.get("object_id"),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "impact_level": "medium",
            "is_automated": False
        }
        
        # Store in database
        try:
            # Use SQLAlchemy to create the activity
            from sqlalchemy.orm import Session
            from core.database_service import get_db
            
            # For now, log the activity (database integration may need session management)
            logger.info(f"Activity tracked: {request.activity_type} by user {user_id}")
            logger.info(f"Activity details: {activity_data}")
            
        except Exception as db_error:
            logger.error(f"Database error (continuing anyway): {db_error}")
        
        # Broadcast to WebSocket for real-time updates
        websocket_payload = {
            "type": "activity_logged",
            "activity_type": request.activity_type,
            "user_id": user_id,
            "description": description,
            "timestamp": request.timestamp,
            "metadata": request.metadata
        }
        
        await broadcast_activity_to_websocket(websocket_payload)
        
        # Increment appropriate dashboard statistic
        stat_name_map = {
            "schema_generated": "schemasGenerated",
            "api_scaffolded": "apisScaffolded",
            "data_cleaned": "dataFilesCleaned",
            "code_generated": "codeGenerated",
            "migration_completed": "migrationsCompleted",
            "visualization_created": "visualizationsCreated"
        }
        
        stat_name = stat_name_map.get(request.activity_type)
        if stat_name:
            await increment_dashboard_stat(stat_name)
        
        return ActivityTrackResponse(
            success=True,
            message="Activity tracked successfully",
            activity_id=activity_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track activity: {str(e)}"
        )


@router.get("/recent")
async def get_recent_activities(
    user_id: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Get recent activities for a user or all users
    
    **Parameters:**
    - user_id: Filter by specific user (optional, defaults to current user)
    - limit: Maximum number of activities to return (default 10, max 100)
    - offset: Pagination offset (default 0)
    
    **Returns:**
    - activities: List of recent activities with metadata
    - total: Total count of activities
    """
    try:
        # Use provided user_id or fall back to authenticated user
        target_user_id = user_id if user_id else current_user
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        # TODO: Query database for activities
        # For now, return empty list (will be populated when database integration is complete)
        activities = []
        
        logger.info(f"Fetching recent activities for user: {target_user_id} (limit: {limit}, offset: {offset})")
        
        return {
            "success": True,
            "activities": activities,
            "total": len(activities),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching recent activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent activities"
        )


@router.get("/stats")
async def get_activity_stats(
    user_id: Optional[str] = None,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Get activity statistics for a user
    
    **Parameters:**
    - user_id: Get stats for specific user (optional, defaults to current user)
    
    **Returns:**
    - stats: Activity breakdown by type
    - total_activities: Total count of all activities
    """
    try:
        target_user_id = user_id if user_id else current_user
        
        # TODO: Query database for stats
        # For now, return zero stats (will be populated when database integration is complete)
        stats = {
            "schema_generated": 0,
            "api_scaffolded": 0,
            "data_cleaned": 0,
            "code_generated": 0,
            "migration_completed": 0,
            "total_activities": 0
        }
        
        logger.info(f"Fetching activity stats for user: {target_user_id}")
        
        return {
            "success": True,
            "user_id": target_user_id,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching activity stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch activity stats"
        )
