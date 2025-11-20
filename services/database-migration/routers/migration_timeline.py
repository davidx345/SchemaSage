"""
Migration Timeline Router

Endpoint: POST /api/migration/timeline
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from models.timeline_models import (
    TimelineRequest,
    TimelineResponse,
    ErrorResponse
)
from core.timeline.generator import generate_timeline
from core.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migration", tags=["migration-timeline"])


@router.post("/timeline", response_model=TimelineResponse)
async def generate_migration_timeline(
    request: TimelineRequest,
    user_id: int = Depends(get_current_user_optional)
):
    """
    Generate detailed migration timeline with phases, resources, and risks
    
    Args:
        request: Migration timeline request
        user_id: Optional authenticated user ID
        
    Returns:
        TimelineResponse with phases, resources, risks, and recommendations
    """
    try:
        logger.info(
            f"Generating migration timeline for user {user_id}: "
            f"{request.source_db_type} -> {request.target_db_type}, "
            f"{request.data_volume_gb}GB, {request.num_tables} tables"
        )
        
        # Generate timeline
        summary, phases, resources, risks, recommendations = generate_timeline(request)
        
        # Build response
        response = TimelineResponse(
            success=True,
            summary=summary,
            phases=phases,
            resource_requirements=resources,
            risks=risks,
            recommendations=recommendations,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Timeline generated: {summary.total_phases} phases, "
            f"{summary.total_duration_days} days, "
            f"complexity={summary.complexity_level.value}, "
            f"risk={summary.overall_risk_level.value}"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        error_response = ErrorResponse(
            error="Validation error",
            details=str(e)
        )
        return JSONResponse(
            status_code=400,
            content=error_response.dict()
        )
        
    except Exception as e:
        logger.error(f"Error generating timeline: {e}", exc_info=True)
        error_response = ErrorResponse(
            error="Failed to generate migration timeline",
            details=str(e)
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )


@router.get("/timeline/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "migration-timeline-generator"}
