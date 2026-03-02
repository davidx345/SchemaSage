"""
Schema diff visualization endpoint.
Compares schemas and provides detailed difference analysis.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.diff_models import DiffRequest, DiffResponse
from core.diff import compare_schemas
from core.auth import get_current_user_optional

router = APIRouter(prefix="/api/schema", tags=["schema"])
logger = logging.getLogger(__name__)


@router.post("/diff", response_model=DiffResponse)
async def schema_diff_endpoint(
    request: DiffRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Compare two schemas and visualize differences.
    
    Generates detailed difference report with migration actions,
    impact analysis, and compatibility assessment.
    """
    try:
        logger.info("Comparing schemas for diff visualization")
        
        # Call diff service
        (summary, statistics, table_diffs, index_diffs, constraint_diffs,
         view_diffs, migration_actions, visualization_data, warnings,
         recommendations) = compare_schemas(
            source_schema=request.source_schema,
            target_schema=request.target_schema,
            output_format=request.output_format,
            show_unchanged=request.show_unchanged,
            detail_level=request.detail_level,
            compare_data_types=request.compare_data_types,
            compare_constraints=request.compare_constraints,
            compare_indexes=request.compare_indexes
        )
        
        # Build response
        response = DiffResponse(
            summary=summary,
            statistics=statistics,
            table_diffs=table_diffs,
            index_diffs=index_diffs,
            constraint_diffs=constraint_diffs,
            view_diffs=view_diffs,
            migration_actions=migration_actions,
            visualization_data=visualization_data if visualization_data else None,
            warnings=warnings,
            recommendations=recommendations
        )
        
        logger.info(
            f"Schema diff complete: {statistics.total_tables} tables compared, "
            f"compatibility: {summary.compatibility_score}%"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in schema diff: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error comparing schemas: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to compare schemas",
                "detail": str(e)
            }
        )
