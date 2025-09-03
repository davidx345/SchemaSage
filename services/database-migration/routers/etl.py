"""
ETL & Data Processing API Routes
Handles ETL pipeline management, execution, and monitoring
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/etl", tags=["ETL & Data Processing"])

# ETL Pipeline Models
class PipelineStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

class PipelineType(str, Enum):
    BATCH = "batch"
    STREAMING = "streaming"
    INCREMENTAL = "incremental"
    FULL_LOAD = "full_load"

# In-memory storage for demo (use database in production)
pipelines_store = {}
pipeline_executions = {}
etl_stats = {
    "total_pipelines": 0,
    "active_pipelines": 0,
    "successful_executions": 0,
    "failed_executions": 0,
    "data_processed_gb": 0.0,
    "avg_execution_time_minutes": 0.0
}

def create_sample_pipeline(pipeline_id: str, name: str) -> Dict[str, Any]:
    """Create a sample ETL pipeline"""
    return {
        "id": pipeline_id,
        "name": name,
        "description": f"ETL pipeline for {name}",
        "type": PipelineType.BATCH.value,
        "status": PipelineStatus.DRAFT.value,
        "source": {
            "type": "database",
            "connection_string": "postgresql://localhost:5432/source_db",
            "tables": ["users", "orders", "products"]
        },
        "destination": {
            "type": "data_warehouse",
            "connection_string": "postgresql://localhost:5432/warehouse_db",
            "schema": "analytics"
        },
        "transformations": [
            {
                "name": "clean_data",
                "type": "data_cleaning",
                "rules": ["remove_duplicates", "handle_nulls", "standardize_formats"]
            },
            {
                "name": "aggregate_metrics",
                "type": "aggregation",
                "fields": ["revenue", "order_count", "customer_segments"]
            }
        ],
        "schedule": {
            "type": "cron",
            "expression": "0 2 * * *",  # Daily at 2 AM
            "timezone": "UTC"
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "created_by": "system",
        "last_execution": None,
        "next_execution": None,
        "execution_count": 0,
        "success_rate": 100.0,
        "avg_duration_minutes": 0.0,
        "data_volume_processed_gb": 0.0
    }

# Initialize sample pipelines
def initialize_sample_pipelines():
    """Initialize sample ETL pipelines"""
    sample_pipelines = [
        ("pipeline_1", "Customer Data Sync"),
        ("pipeline_2", "Order Processing Pipeline"),
        ("pipeline_3", "Product Catalog ETL"),
        ("pipeline_4", "Analytics Data Mart"),
        ("pipeline_5", "Real-time Event Stream")
    ]
    
    for pipeline_id, name in sample_pipelines:
        pipelines_store[pipeline_id] = create_sample_pipeline(pipeline_id, name)
    
    etl_stats["total_pipelines"] = len(pipelines_store)

# Initialize on module load
initialize_sample_pipelines()

@router.get("/pipelines")
async def list_etl_pipelines(
    status: Optional[PipelineStatus] = Query(None, description="Filter by pipeline status"),
    pipeline_type: Optional[PipelineType] = Query(None, description="Filter by pipeline type"),
    limit: int = Query(50, ge=1, le=100, description="Number of pipelines to return"),
    offset: int = Query(0, ge=0, description="Number of pipelines to skip")
):
    """List ETL pipelines with filtering and pagination"""
    try:
        pipelines = list(pipelines_store.values())
        
        # Apply filters
        if status:
            pipelines = [p for p in pipelines if p["status"] == status.value]
        if pipeline_type:
            pipelines = [p for p in pipelines if p["type"] == pipeline_type.value]
        
        # Sort by created_at (newest first)
        pipelines.sort(key=lambda x: x["created_at"], reverse=True)
        
        total = len(pipelines)
        
        # Apply pagination
        paginated_pipelines = pipelines[offset:offset + limit]
        
        return {
            "pipelines": paginated_pipelines,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        logger.error(f"Error listing ETL pipelines: {e}")
        raise HTTPException(status_code=500, detail="Failed to list ETL pipelines")

@router.post("/pipelines")
async def create_etl_pipeline(pipeline_data: Dict[str, Any]):
    """Create a new ETL pipeline"""
    try:
        pipeline_id = str(uuid.uuid4())
        
        pipeline = {
            "id": pipeline_id,
            "name": pipeline_data.get("name", f"Pipeline {pipeline_id[:8]}"),
            "description": pipeline_data.get("description", ""),
            "type": pipeline_data.get("type", PipelineType.BATCH.value),
            "status": PipelineStatus.DRAFT.value,
            "source": pipeline_data.get("source", {}),
            "destination": pipeline_data.get("destination", {}),
            "transformations": pipeline_data.get("transformations", []),
            "schedule": pipeline_data.get("schedule", {}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "created_by": pipeline_data.get("created_by", "user"),
            "last_execution": None,
            "next_execution": None,
            "execution_count": 0,
            "success_rate": 100.0,
            "avg_duration_minutes": 0.0,
            "data_volume_processed_gb": 0.0
        }
        
        pipelines_store[pipeline_id] = pipeline
        etl_stats["total_pipelines"] += 1
        
        logger.info(f"Created ETL pipeline: {pipeline_id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"Error creating ETL pipeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ETL pipeline")

@router.get("/pipelines/{pipeline_id}")
async def get_etl_pipeline(pipeline_id: str):
    """Get a specific ETL pipeline by ID"""
    try:
        if pipeline_id not in pipelines_store:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        return pipelines_store[pipeline_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ETL pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ETL pipeline")

@router.put("/pipelines/{pipeline_id}")
async def update_etl_pipeline(pipeline_id: str, pipeline_data: Dict[str, Any]):
    """Update an existing ETL pipeline"""
    try:
        if pipeline_id not in pipelines_store:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        pipeline = pipelines_store[pipeline_id]
        
        # Update fields
        for key, value in pipeline_data.items():
            if key not in ["id", "created_at", "created_by"]:
                pipeline[key] = value
        
        pipeline["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Updated ETL pipeline: {pipeline_id}")
        return pipeline
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ETL pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ETL pipeline")

@router.delete("/pipelines/{pipeline_id}")
async def delete_etl_pipeline(pipeline_id: str):
    """Delete an ETL pipeline"""
    try:
        if pipeline_id not in pipelines_store:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        del pipelines_store[pipeline_id]
        etl_stats["total_pipelines"] -= 1
        
        logger.info(f"Deleted ETL pipeline: {pipeline_id}")
        return {"message": "Pipeline deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ETL pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete ETL pipeline")

async def execute_pipeline_background(pipeline_id: str):
    """Execute pipeline in background"""
    try:
        pipeline = pipelines_store.get(pipeline_id)
        if not pipeline:
            return
        
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Create execution record
        execution = {
            "id": execution_id,
            "pipeline_id": pipeline_id,
            "status": "running",
            "start_time": start_time.isoformat(),
            "end_time": None,
            "duration_minutes": None,
            "records_processed": 0,
            "data_volume_gb": 0.0,
            "logs": [],
            "error_message": None
        }
        
        pipeline_executions[execution_id] = execution
        pipeline["status"] = PipelineStatus.RUNNING.value
        
        # Simulate pipeline execution
        await asyncio.sleep(2)  # Simulate processing time
        
        # Mark as completed
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        
        execution.update({
            "status": "completed",
            "end_time": end_time.isoformat(),
            "duration_minutes": round(duration, 2),
            "records_processed": 10000,
            "data_volume_gb": 1.5,
            "logs": [
                "Pipeline started successfully",
                "Extracted 10000 records from source",
                "Applied data transformations",
                "Loaded data to destination",
                "Pipeline completed successfully"
            ]
        })
        
        pipeline.update({
            "status": PipelineStatus.COMPLETED.value,
            "last_execution": end_time.isoformat(),
            "execution_count": pipeline["execution_count"] + 1,
            "avg_duration_minutes": round((pipeline["avg_duration_minutes"] + duration) / 2, 2),
            "data_volume_processed_gb": pipeline["data_volume_processed_gb"] + 1.5
        })
        
        # Update global stats
        etl_stats["successful_executions"] += 1
        etl_stats["data_processed_gb"] += 1.5
        
        logger.info(f"Pipeline {pipeline_id} executed successfully")
        
    except Exception as e:
        logger.error(f"Error executing pipeline {pipeline_id}: {e}")
        if execution_id in pipeline_executions:
            pipeline_executions[execution_id]["status"] = "failed"
            pipeline_executions[execution_id]["error_message"] = str(e)
        if pipeline_id in pipelines_store:
            pipelines_store[pipeline_id]["status"] = PipelineStatus.FAILED.value
        etl_stats["failed_executions"] += 1

@router.post("/pipelines/{pipeline_id}/start")
async def start_pipeline(pipeline_id: str, background_tasks: BackgroundTasks):
    """Start pipeline execution"""
    try:
        if pipeline_id not in pipelines_store:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        pipeline = pipelines_store[pipeline_id]
        
        if pipeline["status"] == PipelineStatus.RUNNING.value:
            raise HTTPException(status_code=400, detail="Pipeline is already running")
        
        # Start execution in background
        background_tasks.add_task(execute_pipeline_background, pipeline_id)
        
        etl_stats["active_pipelines"] += 1
        
        return {
            "message": "Pipeline execution started",
            "pipeline_id": pipeline_id,
            "status": "starting"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start pipeline")

@router.post("/pipelines/{pipeline_id}/stop")
async def stop_pipeline(pipeline_id: str):
    """Stop pipeline execution"""
    try:
        if pipeline_id not in pipelines_store:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        pipeline = pipelines_store[pipeline_id]
        
        if pipeline["status"] != PipelineStatus.RUNNING.value:
            raise HTTPException(status_code=400, detail="Pipeline is not running")
        
        pipeline["status"] = PipelineStatus.STOPPED.value
        etl_stats["active_pipelines"] = max(0, etl_stats["active_pipelines"] - 1)
        
        return {
            "message": "Pipeline execution stopped",
            "pipeline_id": pipeline_id,
            "status": "stopped"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop pipeline")

@router.post("/pipelines/{pipeline_id}/pause")
async def pause_pipeline(pipeline_id: str):
    """Pause pipeline execution"""
    try:
        if pipeline_id not in pipelines_store:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        pipeline = pipelines_store[pipeline_id]
        
        if pipeline["status"] != PipelineStatus.RUNNING.value:
            raise HTTPException(status_code=400, detail="Pipeline is not running")
        
        pipeline["status"] = PipelineStatus.PAUSED.value
        
        return {
            "message": "Pipeline execution paused",
            "pipeline_id": pipeline_id,
            "status": "paused"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause pipeline")

@router.post("/pipelines/{pipeline_id}/resume")
async def resume_pipeline(pipeline_id: str):
    """Resume paused pipeline execution"""
    try:
        if pipeline_id not in pipelines_store:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        pipeline = pipelines_store[pipeline_id]
        
        if pipeline["status"] != PipelineStatus.PAUSED.value:
            raise HTTPException(status_code=400, detail="Pipeline is not paused")
        
        pipeline["status"] = PipelineStatus.RUNNING.value
        
        return {
            "message": "Pipeline execution resumed",
            "pipeline_id": pipeline_id,
            "status": "running"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume pipeline")

@router.get("/pipelines/{pipeline_id}/executions")
async def get_pipeline_executions(
    pipeline_id: str,
    limit: int = Query(20, ge=1, le=100, description="Number of executions to return")
):
    """Get execution history for a pipeline"""
    try:
        if pipeline_id not in pipelines_store:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # Filter executions for this pipeline
        executions = [
            exec for exec in pipeline_executions.values() 
            if exec["pipeline_id"] == pipeline_id
        ]
        
        # Sort by start time (newest first)
        executions.sort(key=lambda x: x["start_time"], reverse=True)
        
        # Apply limit
        executions = executions[:limit]
        
        return {
            "executions": executions,
            "total": len(executions),
            "pipeline_id": pipeline_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting executions for pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline executions")

@router.get("/stats")
async def get_etl_statistics():
    """Get ETL statistics and metrics"""
    try:
        # Update active pipelines count
        active_count = sum(1 for p in pipelines_store.values() 
                          if p["status"] == PipelineStatus.RUNNING.value)
        etl_stats["active_pipelines"] = active_count
        
        # Calculate average execution time
        completed_executions = [
            exec for exec in pipeline_executions.values() 
            if exec["status"] == "completed" and exec["duration_minutes"]
        ]
        
        if completed_executions:
            avg_duration = sum(exec["duration_minutes"] for exec in completed_executions) / len(completed_executions)
            etl_stats["avg_execution_time_minutes"] = round(avg_duration, 2)
        
        # Add recent activity
        recent_executions = sorted(
            pipeline_executions.values(),
            key=lambda x: x["start_time"],
            reverse=True
        )[:5]
        
        return {
            "summary": etl_stats,
            "pipeline_status_breakdown": {
                "draft": sum(1 for p in pipelines_store.values() if p["status"] == PipelineStatus.DRAFT.value),
                "running": sum(1 for p in pipelines_store.values() if p["status"] == PipelineStatus.RUNNING.value),
                "paused": sum(1 for p in pipelines_store.values() if p["status"] == PipelineStatus.PAUSED.value),
                "completed": sum(1 for p in pipelines_store.values() if p["status"] == PipelineStatus.COMPLETED.value),
                "failed": sum(1 for p in pipelines_store.values() if p["status"] == PipelineStatus.FAILED.value),
                "stopped": sum(1 for p in pipelines_store.values() if p["status"] == PipelineStatus.STOPPED.value)
            },
            "recent_activity": recent_executions,
            "performance_metrics": {
                "success_rate": round(
                    (etl_stats["successful_executions"] / max(1, etl_stats["successful_executions"] + etl_stats["failed_executions"])) * 100, 2
                ),
                "total_executions": etl_stats["successful_executions"] + etl_stats["failed_executions"],
                "data_throughput_gb_per_hour": round(etl_stats["data_processed_gb"] / max(1, etl_stats["avg_execution_time_minutes"] / 60), 2) if etl_stats["avg_execution_time_minutes"] > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting ETL statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ETL statistics")

@router.get("/pipelines/{pipeline_id}/logs")
async def get_pipeline_logs(
    pipeline_id: str,
    execution_id: Optional[str] = Query(None, description="Specific execution ID")
):
    """Get logs for pipeline execution"""
    try:
        if pipeline_id not in pipelines_store:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        if execution_id:
            if execution_id not in pipeline_executions:
                raise HTTPException(status_code=404, detail="Execution not found")
            execution = pipeline_executions[execution_id]
            return {
                "execution_id": execution_id,
                "pipeline_id": pipeline_id,
                "logs": execution.get("logs", []),
                "status": execution["status"]
            }
        else:
            # Get logs from latest execution
            latest_execution = None
            for exec in pipeline_executions.values():
                if exec["pipeline_id"] == pipeline_id:
                    if not latest_execution or exec["start_time"] > latest_execution["start_time"]:
                        latest_execution = exec
            
            if latest_execution:
                return {
                    "execution_id": latest_execution["id"],
                    "pipeline_id": pipeline_id,
                    "logs": latest_execution.get("logs", []),
                    "status": latest_execution["status"]
                }
            else:
                return {
                    "execution_id": None,
                    "pipeline_id": pipeline_id,
                    "logs": ["No executions found for this pipeline"],
                    "status": "no_executions"
                }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline logs")
