"""
Query Cost Analyzer Router

Endpoint: POST /api/query/analyze-cost
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from models.query_models import (
    QueryCostRequest,
    QueryCostResponse,
    QueryAnalysis,
    ErrorResponse
)
from core.query.parser import parse_query
from core.query.cost_estimator import estimate_query_cost, OptimizationEngine
from core.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/query", tags=["query-analysis"])


@router.post("/analyze-cost", response_model=QueryCostResponse)
async def analyze_query_cost(
    request: QueryCostRequest,
    user_id: int = Depends(get_current_user_optional)
):
    """
    Analyze SQL query cost and provide optimization suggestions
    
    Args:
        request: Query cost analysis request
        user_id: Optional authenticated user ID
        
    Returns:
        QueryCostResponse with cost breakdown and optimization suggestions
    """
    try:
        logger.info(f"Analyzing query cost for user {user_id}: {request.query[:100]}...")
        
        # Parse the query
        parsed_query = parse_query(request.query)
        
        # Estimate costs
        cost_breakdown, execution_stats = estimate_query_cost(
            parsed_query,
            request.schema_info
        )
        
        # Generate query analysis
        query_analysis = QueryAnalysis(
            query_type=parsed_query["query_type"],
            complexity_score=parsed_query["complexity_score"],
            issues_found=0,  # Will be calculated from suggestions
            critical_issues=0
        )
        
        # Generate optimization suggestions
        optimizations = []
        if request.include_optimizations:
            optimizations = OptimizationEngine.generate_suggestions(
                parsed_query,
                execution_stats,
                cost_breakdown
            )
            
            # Count issues by severity
            query_analysis.issues_found = len(optimizations)
            query_analysis.critical_issues = sum(
                1 for opt in optimizations if opt.severity.value == "critical"
            )
        
        # Build response
        response = QueryCostResponse(
            success=True,
            query_analysis=query_analysis,
            cost_breakdown=cost_breakdown,
            execution_stats=execution_stats,
            optimizations=optimizations,
            optimized_query=None,  # Future: Auto-generate optimized query
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Query analysis complete: complexity={parsed_query['complexity_score']}, "
            f"cost={cost_breakdown.total_cost}, issues={len(optimizations)}"
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
        logger.error(f"Error analyzing query cost: {e}", exc_info=True)
        error_response = ErrorResponse(
            error="Failed to analyze query cost",
            details=str(e)
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "query-cost-analyzer"}
