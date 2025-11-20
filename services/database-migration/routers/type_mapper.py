"""
Data Type Mapper Router

Endpoint: POST /api/migration/map-types
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from models.type_mapping_models import (
    TypeMappingRequest,
    TypeMappingResponse,
    ErrorResponse
)
from core.type_mapping.mapper import map_data_types
from core.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migration", tags=["type-mapping"])


@router.post("/map-types", response_model=TypeMappingResponse)
async def map_data_type_mappings(
    request: TypeMappingRequest,
    user_id: int = Depends(get_current_user_optional)
):
    """
    Map data types between source and target databases
    
    Args:
        request: Data type mapping request
        user_id: Optional authenticated user ID
        
    Returns:
        TypeMappingResponse with detailed type mappings, warnings, and recommendations
    """
    try:
        logger.info(
            f"Mapping data types for user {user_id}: "
            f"{request.source_db_type} -> {request.target_db_type}, "
            f"{len(request.source_types)} types"
        )
        
        # Map types
        summary, mappings, recommendations, unsupported_types = map_data_types(request)
        
        # Build response
        response = TypeMappingResponse(
            success=True,
            summary=summary,
            mappings=mappings,
            general_recommendations=recommendations,
            unsupported_types=unsupported_types,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Type mapping complete: {summary.total_types} types, "
            f"{summary.exact_mappings} exact, "
            f"{summary.lossy_mappings} lossy, "
            f"confidence={summary.overall_confidence.value}, "
            f"risk={summary.overall_data_loss_risk.value}"
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
        logger.error(f"Error mapping types: {e}", exc_info=True)
        error_response = ErrorResponse(
            error="Failed to map data types",
            details=str(e)
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )


@router.get("/map-types/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-type-mapper"}
