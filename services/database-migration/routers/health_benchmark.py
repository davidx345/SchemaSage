"""
Health Benchmark Router.
Handles performance scoring, health timeline, and slow query analysis.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.health_models import (
    PerformanceScoreRequest, PerformanceScoreResponse,
    HealthTimelineRequest, HealthTimelineResponse,
    SlowQueryRequest, SlowQueryResponse
)
from core.health import PerformanceScorer, TimelineTracker, QueryAnalyzer

router = APIRouter(prefix="/api/health", tags=["health"])
logger = logging.getLogger(__name__)

# Initialize core services
performance_scorer = PerformanceScorer()
timeline_tracker = TimelineTracker()
query_analyzer = QueryAnalyzer()

@router.post("/performance-score", response_model=PerformanceScoreResponse)
async def get_performance_score(request: PerformanceScoreRequest):
    """
    Calculates weighted database performance score across multiple categories.
    """
    try:
        logger.info(f"Calculating performance score for {request.database_type}")
        
        result = performance_scorer.calculate_score(
            request.database_type,
            request.connection_string,
            request.include_recommendations
        )
        
        return PerformanceScoreResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error calculating performance score: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/timeline", response_model=HealthTimelineResponse)
async def get_health_timeline(request: HealthTimelineRequest):
    """
    Returns health metrics over time with trend analysis and forecasting.
    """
    try:
        logger.info(f"Fetching health timeline for {request.days} days")
        
        result = timeline_tracker.track_timeline(
            request.database_type,
            request.connection_string,
            request.days,
            request.include_forecast
        )
        
        return HealthTimelineResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error fetching health timeline: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/slow-queries", response_model=SlowQueryResponse)
async def analyze_slow_queries(request: SlowQueryRequest):
    """
    Analyzes slow queries and provides optimization recommendations.
    """
    try:
        logger.info(f"Analyzing slow queries with threshold {request.threshold_ms}ms")
        
        result = query_analyzer.analyze_queries(
            request.database_type,
            request.connection_string,
            request.threshold_ms,
            request.limit,
            request.include_explain
        )
        
        return SlowQueryResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error analyzing slow queries: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
