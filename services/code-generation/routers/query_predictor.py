"""
Query performance predictor endpoint.
Predicts query performance and provides optimization guidance.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.predictor_models import PredictorRequest, PredictorResponse
from core.predictor import predict_query_performance
from core.auth import get_current_user_optional

router = APIRouter(prefix="/api/query", tags=["query"])
logger = logging.getLogger(__name__)


@router.post("/predict-performance", response_model=PredictorResponse)
async def query_predictor_endpoint(
    request: PredictorRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Predict query performance and provide optimization suggestions.
    
    Analyzes SQL queries, predicts performance metrics, identifies bottlenecks,
    and provides detailed optimization recommendations.
    """
    try:
        logger.info(f"Predicting performance for {request.database_engine} query")
        
        # Call predictor service
        (query_analysis, performance_metrics, bottlenecks, suggestions,
         index_recommendations, comparison, summary, warnings) = predict_query_performance(
            sql_query=request.sql_query,
            database_engine=request.database_engine,
            table_statistics=request.table_statistics,
            query_type=request.query_type,
            expected_result_rows=request.expected_result_rows,
            concurrent_queries=request.concurrent_queries
        )
        
        # Build response
        response = PredictorResponse(
            query_analysis=query_analysis,
            performance_metrics=performance_metrics,
            bottlenecks=bottlenecks,
            optimization_suggestions=suggestions,
            index_recommendations=index_recommendations,
            comparison=comparison,
            summary=summary,
            warnings=warnings
        )
        
        logger.info(
            f"Performance prediction complete: {performance_metrics.performance_rating.value}, "
            f"estimated time: {performance_metrics.estimated_execution_time_ms}ms"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in performance prediction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error predicting performance: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to predict query performance",
                "detail": str(e)
            }
        )
