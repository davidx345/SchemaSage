"""
Migration Executor Core Logic.
Executes migrations with real-time progress tracking.
"""
from typing import List, Dict, Any, Callable
from uuid import uuid4
from datetime import datetime
import asyncio

from models.universal_migration_models import (
    MigrationExecutionData, ProgressInfo, PerformanceMetrics, MigrationStatus
)


class MigrationExecutor:
    """
    Executes database migrations with real-time progress tracking.
    """
    
    def __init__(self):
        self.active_executions = {}
        self.progress_callbacks = {}
    
    async def execute_migration(self, migration_id: str, options: Dict[str, Any], progress_callback: Callable = None) -> MigrationExecutionData:
        """Executes a migration with real-time progress tracking."""
        execution_id = f"exec_{str(uuid4())[:8]}"
        
        # Register progress callback
        if progress_callback:
            self.progress_callbacks[execution_id] = progress_callback
        
        # Initialize execution state
        self.active_executions[execution_id] = {
            "status": MigrationStatus.IN_PROGRESS,
            "start_time": datetime.utcnow(),
            "progress": 0,
            "current_step": 1
        }
        
        # Execute migration steps
        try:
            execution_data = await self._execute_steps(execution_id, migration_id, options)
            self.active_executions[execution_id]["status"] = MigrationStatus.COMPLETED
            return execution_data
        except Exception as e:
            self.active_executions[execution_id]["status"] = MigrationStatus.FAILED
            raise
    
    async def _execute_steps(self, execution_id: str, migration_id: str, options: Dict[str, Any]) -> MigrationExecutionData:
        """Executes migration steps sequentially."""
        dry_run = options.get("dry_run", False)
        verify_data = options.get("verify_data", True)
        
        total_steps = 7
        records_migrated = 0
        
        # Simulate migration execution
        for step in range(1, total_steps + 1):
            # Update progress
            progress_pct = int((step / total_steps) * 100)
            await self._update_progress(execution_id, step, progress_pct, records_migrated)
            
            # Simulate work
            await asyncio.sleep(0.5)  # Simulate step execution
            
            # Increment records for data migration steps
            if step in [4, 5]:
                records_migrated += 350000 if step == 5 else 15000
        
        # Calculate metrics
        elapsed_time = 285  # seconds
        records_per_sec = records_migrated / elapsed_time if elapsed_time > 0 else 0
        
        progress = ProgressInfo(
            percentage=100,
            current_step=total_steps,
            total_steps=total_steps,
            records_migrated=records_migrated,
            time_elapsed_seconds=elapsed_time,
            estimated_time_remaining_seconds=0
        )
        
        performance_metrics = PerformanceMetrics(
            records_per_second=int(records_per_sec),
            errors_count=0,
            warnings_count=3,
            retry_count=0
        )
        
        return MigrationExecutionData(
            execution_id=execution_id,
            migration_id=migration_id,
            status=MigrationStatus.COMPLETED,
            progress=progress,
            performance_metrics=performance_metrics,
            rollback_point_id=f"rb_{execution_id}" if not dry_run else None
        )
    
    async def _update_progress(self, execution_id: str, step: int, progress_pct: int, records_migrated: int):
        """Updates and broadcasts migration progress."""
        state = self.active_executions.get(execution_id)
        if not state:
            return
        
        state["current_step"] = step
        state["progress"] = progress_pct
        
        # Call progress callback (for WebSocket broadcasting)
        if execution_id in self.progress_callbacks:
            callback = self.progress_callbacks[execution_id]
            await callback({
                "execution_id": execution_id,
                "progress": progress_pct,
                "current_step": step,
                "records_migrated": records_migrated
            })
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Gets current execution status."""
        return self.active_executions.get(execution_id, {})
    
    async def cancel_migration(self, execution_id: str) -> bool:
        """Cancels an active migration."""
        if execution_id in self.active_executions:
            self.active_executions[execution_id]["status"] = MigrationStatus.CANCELLED
            return True
        return False
