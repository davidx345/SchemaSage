"""
Migration monitoring endpoint.
Provides real-time monitoring of migration operations.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from datetime import datetime

from models.monitor_models import MonitorRequest, MonitorResponse
from core.monitor import monitor_migration
from core.auth import get_current_user_optional

router = APIRouter(prefix="/api/migration", tags=["migration"])
logger = logging.getLogger(__name__)


@router.post("/monitor", response_model=MonitorResponse)
async def monitor_migration_endpoint(
    request: MonitorRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Monitor real-time migration progress and performance.
    
    Tracks migration status, progress metrics, performance data,
    issues, resource utilization, and provides recommendations.
    """
    try:
        logger.info(f"Monitoring migration: {request.migration_id}")
        
        # Call monitoring service
        summary, progress, performance, issues, resources, logs, recommendations = monitor_migration(
            migration_id=request.migration_id,
            include_metrics=request.include_metrics,
            include_logs=request.include_logs
        )
        
        # Calculate next refresh time
        next_refresh = None
        if request.refresh_interval:
            next_refresh = datetime.now().replace(microsecond=0)
            from datetime import timedelta
            next_refresh += timedelta(seconds=request.refresh_interval)
        
        # Build response
        response = MonitorResponse(
            summary=summary,
            progress=progress,
            performance=performance,
            issues=issues,
            resources=resources,
            logs=logs if request.include_logs else None,
            recommendations=recommendations,
            next_refresh=next_refresh
        )
        
        logger.info(
            f"Migration {request.migration_id} status: {summary.status}, "
            f"progress: {progress.percentage_complete}%"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in migration monitoring: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error monitoring migration: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to monitor migration",
                "detail": str(e),
                "migration_id": request.migration_id
            }
        )
