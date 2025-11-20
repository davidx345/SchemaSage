"""
Index recommendation endpoint.
Analyzes workloads and recommends optimal indexes.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.index_models import IndexRecommendationRequest, IndexRecommendationResponse
from core.indexing import recommend_indexes_for_workload
from core.auth import get_current_user_optional

router = APIRouter(prefix="/api/schema", tags=["schema"])
logger = logging.getLogger(__name__)


@router.post("/recommend-indexes", response_model=IndexRecommendationResponse)
async def index_recommendation_endpoint(
    request: IndexRecommendationRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Analyze workload and recommend optimal indexes.
    
    Examines query patterns, column usage, and existing indexes to provide
    intelligent index recommendations that improve query performance.
    """
    try:
        logger.info(
            f"Generating index recommendations for {len(request.table_workloads)} tables "
            f"with {request.optimization_goal} goal"
        )
        
        # Call index recommendation engine
        (recommendations, covering_indexes, redundant, missing_patterns,
         maintenance, workload_analysis, statistics, warnings) = recommend_indexes_for_workload(
            database_engine=request.database_engine,
            table_workloads=request.table_workloads,
            existing_indexes=request.existing_indexes,
            workload_patterns=request.workload_patterns,
            min_improvement_threshold=request.min_improvement_threshold,
            max_recommendations=request.max_recommendations,
            optimization_goal=request.optimization_goal
        )
        
        # Build response
        response = IndexRecommendationResponse(
            recommendations=recommendations,
            covering_index_recommendations=covering_indexes,
            redundant_indexes=redundant,
            missing_index_patterns=missing_patterns,
            maintenance_recommendations=maintenance,
            workload_analysis=workload_analysis,
            statistics=statistics,
            warnings=warnings
        )
        
        logger.info(
            f"Index analysis complete: {len(recommendations)} recommendations, "
            f"{len(redundant)} redundant indexes found"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in index recommendation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error generating index recommendations: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to generate index recommendations",
                "detail": str(e)
            }
        )
