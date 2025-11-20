"""
Performance benchmark endpoint.
Tests and compares query performance across databases.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.benchmark_models import BenchmarkRequest, BenchmarkResponse
from core.benchmark import run_benchmark
from core.auth import get_current_user_optional

router = APIRouter(prefix="/api/performance", tags=["performance"])
logger = logging.getLogger(__name__)


@router.post("/benchmark", response_model=BenchmarkResponse)
async def performance_benchmark_endpoint(
    request: BenchmarkRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Run performance benchmarks comparing source and target databases.
    
    Tests query performance, throughput, concurrency, and resource utilization
    to provide comprehensive performance comparison and recommendations.
    """
    try:
        logger.info(
            f"Running benchmark: {request.source_db_type} vs {request.target_db_type}, "
            f"{len(request.queries)} queries, {request.iterations} iterations"
        )
        
        # Call benchmark service
        (summary, statistics, query_results, source_throughput, target_throughput,
         source_concurrency, target_concurrency, source_resources, target_resources,
         warnings, recommendations) = run_benchmark(
            source_db_type=request.source_db_type,
            target_db_type=request.target_db_type,
            benchmark_type=request.benchmark_type,
            queries=request.queries,
            iterations=request.iterations,
            concurrent_users=request.concurrent_users,
            warm_up_iterations=request.warm_up_iterations,
            timeout_seconds=request.timeout_seconds
        )
        
        # Build response
        response = BenchmarkResponse(
            summary=summary,
            statistics=statistics,
            query_results=query_results,
            source_throughput=source_throughput,
            target_throughput=target_throughput,
            source_concurrency=source_concurrency,
            target_concurrency=target_concurrency,
            source_resources=source_resources,
            target_resources=target_resources,
            warnings=warnings,
            recommendations=recommendations
        )
        
        logger.info(
            f"Benchmark complete: {summary.overall_winner} winner, "
            f"{statistics.total_executions} total executions"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in benchmark: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error running benchmark: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to run performance benchmark",
                "detail": str(e)
            }
        )
