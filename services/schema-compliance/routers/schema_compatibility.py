"""
Schema Compatibility Router

Endpoint: POST /api/schema/compatibility
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from models.compatibility_models import (
    CompatibilityRequest,
    CompatibilityResponse,
    ErrorResponse
)
from core.compatibility.checker import check_compatibility
from core.auth import get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schema", tags=["schema-compatibility"])


@router.post("/compatibility", response_model=CompatibilityResponse)
async def check_schema_compatibility(
    request: CompatibilityRequest,
    user_id: int = Depends(get_optional_user)
):
    """
    Check schema compatibility between source and target databases
    
    Args:
        request: Schema compatibility check request
        user_id: Optional authenticated user ID
        
    Returns:
        CompatibilityResponse with issues, recommendations, and compatibility summary
    """
    try:
        logger.info(
            f"Checking schema compatibility for user {user_id}: "
            f"{request.source_db_type} -> {request.target_db_type}"
        )
        
        # Check compatibility
        summary, issues, recommendations, supported_features, unsupported_features = check_compatibility(request)
        
        # Build response
        response = CompatibilityResponse(
            success=True,
            summary=summary,
            issues=issues,
            recommendations=recommendations,
            supported_features=supported_features,
            unsupported_features=unsupported_features,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Compatibility check complete: {summary.overall_compatibility.value}, "
            f"{summary.total_issues} issues, "
            f"{summary.compatibility_percentage}% compatible"
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
        logger.error(f"Error checking compatibility: {e}", exc_info=True)
        error_response = ErrorResponse(
            error="Failed to check schema compatibility",
            details=str(e)
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )


@router.get("/compatibility/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "schema-compatibility-checker"}
