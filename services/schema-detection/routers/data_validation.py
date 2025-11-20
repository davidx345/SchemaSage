"""
Data validation endpoint.
Validates data quality, integrity, and business rules.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.validation_models import ValidationRequest, ValidationResponse
from core.validation import validate_database_data
from core.auth import get_current_user_optional

router = APIRouter(prefix="/api/validation", tags=["validation"])
logger = logging.getLogger(__name__)


@router.post("/validate-data", response_model=ValidationResponse)
async def data_validation_endpoint(
    request: ValidationRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Execute comprehensive data validation.
    
    Validates schema compliance, data integrity, referential integrity,
    and data quality. Provides detailed reports with actionable recommendations.
    """
    try:
        logger.info(
            f"Starting data validation for {len(request.validation_specs)} tables "
            f"with {len(request.validation_types)} validation types"
        )
        
        # Call validation suite
        (issues, duplicates, quality_metrics, column_stats,
         integrity_results, statistics, summary, warnings) = validate_database_data(
            connection_string=request.database_connection,
            validation_specs=request.validation_specs,
            validation_types=request.validation_types,
            sample_size=request.sample_size,
            fail_fast=request.fail_fast,
            parallel_execution=request.parallel_execution
        )
        
        # Build response
        response = ValidationResponse(
            validation_issues=issues,
            duplicate_records=duplicates,
            quality_metrics=quality_metrics,
            column_statistics=column_stats,
            integrity_check_results=integrity_results,
            statistics=statistics,
            summary=summary,
            warnings=warnings
        )
        
        logger.info(
            f"Validation complete: {statistics.failed_validations} issues found, "
            f"quality score: {quality_metrics.overall_quality_score:.1f}%"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in data validation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error during data validation: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to execute data validation",
                "detail": str(e)
            }
        )
