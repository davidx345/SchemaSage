"""
Migration rollback planner endpoint.
Creates detailed rollback plans for migration operations.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.rollback_models import RollbackRequest, RollbackResponse
from core.rollback import generate_rollback_plan
from core.auth import get_current_user_optional

router = APIRouter(prefix="/api/migration", tags=["migration"])
logger = logging.getLogger(__name__)


@router.post("/rollback-plan", response_model=RollbackResponse)
async def migration_rollback_endpoint(
    request: RollbackRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Generate comprehensive rollback plan for migration.
    
    Creates detailed rollback strategy including steps, timeline,
    risk assessment, data recovery plan, and resource requirements.
    """
    try:
        logger.info(f"Generating rollback plan for migration: {request.migration_id}")
        
        # Call rollback planner
        (summary, risk_assessment, prerequisites, steps, timeline, data_recovery,
         validations, resource_requirements, warnings, recommendations,
         emergency_contacts) = generate_rollback_plan(
            migration_id=request.migration_id,
            migration_state=request.migration_state,
            source_db_type=request.source_db_type,
            target_db_type=request.target_db_type,
            include_data_recovery=request.include_data_recovery,
            max_downtime_minutes=request.max_downtime_minutes,
            preserve_target_changes=request.preserve_target_changes
        )
        
        # Build response
        response = RollbackResponse(
            summary=summary,
            risk_assessment=risk_assessment,
            prerequisites=prerequisites,
            steps=steps,
            timeline=timeline,
            data_recovery=data_recovery,
            validations=validations,
            resource_requirements=resource_requirements,
            warnings=warnings,
            recommendations=recommendations,
            emergency_contacts=emergency_contacts
        )
        
        logger.info(
            f"Rollback plan generated: {summary.complexity.value} complexity, "
            f"{summary.total_steps} steps, {summary.estimated_total_duration_minutes} minutes"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in rollback planning: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error generating rollback plan: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to generate rollback plan",
                "detail": str(e),
                "migration_id": request.migration_id
            }
        )
