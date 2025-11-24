"""
Universal Migration Center Router.
Handles cross-database migration planning, execution, and rollback.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio

from models.universal_migration_models import (
    MigrationPlanRequest, MigrationPlanResponse,
    MigrationExecuteRequest, MigrationExecuteResponse,
    MultiCloudCompareRequest, MultiCloudCompareResponse,
    PreAnalysisRequest, PreAnalysisResponse,
    RollbackRequest, RollbackResponse
)
from core.universal_migration import (
    MigrationPlanner,
    MigrationExecutor,
    MultiCloudComparator,
    PreMigrationAnalyzer,
    RollbackManager
)

router = APIRouter(prefix="/api/migration", tags=["Universal Migration Center"])

# Initialize core components
migration_planner = MigrationPlanner()
migration_executor = MigrationExecutor()
cloud_comparator = MultiCloudComparator()
pre_analyzer = PreMigrationAnalyzer()
rollback_manager = RollbackManager()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, execution_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[execution_id] = websocket
    
    def disconnect(self, execution_id: str):
        if execution_id in self.active_connections:
            del self.active_connections[execution_id]
    
    async def send_progress(self, execution_id: str, message: dict):
        if execution_id in self.active_connections:
            try:
                await self.active_connections[execution_id].send_json(message)
            except Exception:
                self.disconnect(execution_id)

ws_manager = ConnectionManager()


@router.post("/plan", response_model=MigrationPlanResponse)
async def create_migration_plan(request: MigrationPlanRequest):
    """
    Generate a comprehensive migration plan for cross-database migrations.
    
    **Features:**
    - Analyzes source and target databases
    - Generates step-by-step migration plan
    - Identifies compatibility issues and required transformations
    - Supports PostgreSQL, MySQL, MongoDB, SQL Server, Oracle
    """
    try:
        plan_data = migration_planner.create_plan(
            source_url=request.source_connection,
            target_url=request.target_connection,
            migration_type=request.migration_type,
            options=request.options or {}
        )
        
        return MigrationPlanResponse(
            status="success",
            message="Migration plan generated successfully",
            data=plan_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create migration plan: {str(e)}")


@router.post("/execute", response_model=MigrationExecuteResponse)
async def execute_migration(request: MigrationExecuteRequest):
    """
    Execute migration with real-time progress tracking via WebSocket.
    
    **Features:**
    - Step-by-step migration execution
    - Real-time progress updates
    - Performance metrics tracking
    - Automatic checkpoint creation for rollback
    - Dry-run mode for testing
    
    **WebSocket:** Connect to `wss://api/ws/migration/{execution_id}` for live progress updates
    """
    try:
        # Create progress callback for WebSocket updates
        async def progress_callback(progress_data: dict):
            await ws_manager.send_progress(progress_data.get("execution_id"), progress_data)
        
        # Execute migration
        execution_data = await migration_executor.execute_migration(
            migration_id=request.migration_id,
            options=request.options or {},
            progress_callback=progress_callback
        )
        
        return MigrationExecuteResponse(
            status="success",
            message=f"Migration {'dry-run' if request.options.get('dry_run') else 'execution'} completed successfully",
            data=execution_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration execution failed: {str(e)}")


@router.post("/multi-cloud-compare", response_model=MultiCloudCompareResponse)
async def compare_cloud_offerings(request: MultiCloudCompareRequest):
    """
    Compare database offerings across AWS, Azure, and GCP.
    
    **Features:**
    - Cost comparison across cloud providers
    - Performance and reliability scoring
    - Feature availability analysis
    - Best value recommendation with estimated savings
    - Supports RDS, Azure SQL, Cloud SQL, DocumentDB, Cosmos DB
    """
    try:
        comparison_data = cloud_comparator.compare_offerings(
            db_type=request.database_type,
            workload_size=request.workload_size,
            required_features=request.required_features or []
        )
        
        return MultiCloudCompareResponse(
            status="success",
            message="Cloud comparison completed successfully",
            data=comparison_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloud comparison failed: {str(e)}")


@router.post("/pre-analysis", response_model=PreAnalysisResponse)
async def analyze_migration_risks(request: PreAnalysisRequest):
    """
    Analyze migration risks and breaking changes before execution.
    
    **Features:**
    - Breaking change detection (schema, relationships, transactions)
    - Performance impact analysis
    - Dependency identification
    - Overall risk assessment
    - Actionable recommendations
    - Estimated downtime calculation
    """
    try:
        analysis_data = pre_analyzer.analyze_migration(
            source_type=request.source_type,
            target_type=request.target_type,
            migration_plan_id=request.migration_plan_id
        )
        
        return PreAnalysisResponse(
            status="success",
            message="Pre-migration analysis completed successfully",
            data=analysis_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pre-migration analysis failed: {str(e)}")


@router.post("/rollback", response_model=RollbackResponse)
async def create_rollback_plan(request: RollbackRequest):
    """
    Generate intelligent rollback plan with checkpoint restoration.
    
    **Features:**
    - Checkpoint-based rollback
    - Data loss risk assessment
    - Step-by-step rollback plan
    - Downtime estimation
    - Multiple checkpoint options
    """
    try:
        rollback_data = rollback_manager.create_rollback_plan(
            migration_id=request.migration_id,
            execution_id=request.execution_id
        )
        
        return RollbackResponse(
            status="success",
            message="Rollback plan generated successfully",
            data=rollback_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create rollback plan: {str(e)}")


@router.post("/rollback/{rollback_id}/execute")
async def execute_rollback(rollback_id: str, checkpoint_id: str = None):
    """
    Execute rollback to restore database to previous checkpoint.
    
    **Parameters:**
    - `rollback_id`: Rollback plan ID from `/rollback` endpoint
    - `checkpoint_id`: (optional) Specific checkpoint to restore to
    
    **Features:**
    - Safe rollback execution
    - Data integrity verification
    - Automatic backup before rollback
    """
    try:
        result = await rollback_manager.execute_rollback(
            rollback_id=rollback_id,
            checkpoint_id=checkpoint_id
        )
        
        return {
            "status": "success",
            "message": "Rollback executed successfully",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback execution failed: {str(e)}")


@router.websocket("/ws/{execution_id}")
async def migration_progress_websocket(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for real-time migration progress updates.
    
    **Connection:** `wss://api/ws/migration/{execution_id}`
    
    **Message Format:**
    ```json
    {
        "execution_id": "exec_abc123",
        "progress": 45,
        "current_step": 3,
        "records_migrated": 125000,
        "status": "in_progress"
    }
    ```
    """
    await ws_manager.connect(execution_id, websocket)
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            # Client can send "ping" to keep alive
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        ws_manager.disconnect(execution_id)
    except Exception as e:
        ws_manager.disconnect(execution_id)
        print(f"WebSocket error for {execution_id}: {e}")
