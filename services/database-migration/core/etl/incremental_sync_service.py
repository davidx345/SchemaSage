"""
Incremental Sync Service Module
Incremental data synchronization with change detection and conflict resolution.
"""
from typing import Dict, Any, List
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.data_migration import IncrementalSync
from ...core.database import DatabaseManager
from ...utils.logging import get_logger

logger = get_logger(__name__)

class IncrementalSyncService:
    """Incremental data synchronization service."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def execute_incremental_sync(
        self, 
        sync_config: IncrementalSync,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute incremental data synchronization."""
        
        source_conn = await self.db_manager.get_connection(sync_config.source_connection_id)
        target_conn = await self.db_manager.get_connection(sync_config.target_connection_id)
        
        sync_result = {
            "sync_id": sync_config.sync_id,
            "started_at": datetime.utcnow(),
            "rows_processed": 0,
            "rows_inserted": 0,
            "rows_updated": 0,
            "rows_deleted": 0,
            "conflicts": []
        }
        
        try:
            # Get last sync timestamp
            last_sync = await self._get_last_sync_timestamp(sync_config, session)
            
            # Extract changes since last sync
            changes = await self._extract_changes(source_conn, sync_config, last_sync)
            
            # Apply changes to target
            for change in changes:
                await self._apply_change(target_conn, sync_config, change, sync_result)
            
            # Update sync timestamp
            await self._update_sync_timestamp(sync_config, session)
            
            sync_result["completed_at"] = datetime.utcnow()
            sync_result["status"] = "completed"
            
        except Exception as e:
            sync_result["status"] = "failed"
            sync_result["error_message"] = str(e)
            logger.error(f"Incremental sync failed: {e}")
        
        return sync_result
    
    async def _extract_changes(
        self, 
        source_conn: Any, 
        sync_config: IncrementalSync,
        last_sync: datetime
    ) -> List[Dict[str, Any]]:
        """Extract changes from source since last sync."""
        
        if sync_config.change_detection_method == "timestamp":
            query = f"""
            SELECT *, '{sync_config.change_tracking_column}' as change_timestamp
            FROM {sync_config.source_table}
            WHERE {sync_config.change_tracking_column} > %s
            ORDER BY {sync_config.change_tracking_column}
            """
            
            async with source_conn.execute(text(query), (last_sync,)) as result:
                return [dict(row) for row in await result.fetchall()]
        
        elif sync_config.change_detection_method == "log_based":
            # Implementation for log-based change detection
            return await self._extract_log_based_changes(source_conn, sync_config, last_sync)
        
        else:
            raise ValueError(f"Unsupported change detection method: {sync_config.change_detection_method}")
    
    async def _get_last_sync_timestamp(
        self, 
        sync_config: IncrementalSync, 
        session: AsyncSession
    ) -> datetime:
        """Get the timestamp of the last successful sync."""
        
        # In a real implementation, this would query the sync history table
        # For now, return a default timestamp
        return sync_config.last_sync_timestamp or datetime.min
    
    async def _apply_change(
        self, 
        target_conn: Any, 
        sync_config: IncrementalSync, 
        change: Dict[str, Any], 
        sync_result: Dict[str, Any]
    ):
        """Apply a single change to the target database."""
        
        try:
            # Determine operation type (INSERT, UPDATE, DELETE)
            operation = self._determine_operation(change, sync_config)
            
            if operation == "INSERT":
                await self._execute_insert(target_conn, sync_config, change)
                sync_result["rows_inserted"] += 1
            elif operation == "UPDATE":
                await self._execute_update(target_conn, sync_config, change)
                sync_result["rows_updated"] += 1
            elif operation == "DELETE":
                await self._execute_delete(target_conn, sync_config, change)
                sync_result["rows_deleted"] += 1
            
            sync_result["rows_processed"] += 1
            
        except Exception as e:
            # Handle conflicts
            conflict = {
                "row_data": change,
                "operation": operation,
                "error": str(e),
                "conflict_resolution": "skipped"
            }
            sync_result["conflicts"].append(conflict)
            logger.warning(f"Sync conflict: {e}")
    
    def _determine_operation(
        self, 
        change: Dict[str, Any], 
        sync_config: IncrementalSync
    ) -> str:
        """Determine the type of operation for a change."""
        
        # If there's a dedicated operation column, use it
        if sync_config.operation_column and sync_config.operation_column in change:
            return change[sync_config.operation_column].upper()
        
        # Otherwise, default to UPDATE (common for timestamp-based sync)
        return "UPDATE"
    
    async def _execute_insert(
        self, 
        target_conn: Any, 
        sync_config: IncrementalSync, 
        change: Dict[str, Any]
    ):
        """Execute INSERT operation."""
        
        columns = list(change.keys())
        values = list(change.values())
        placeholders = ', '.join(['%s'] * len(values))
        
        query = f"""
        INSERT INTO {sync_config.target_table} ({', '.join(columns)})
        VALUES ({placeholders})
        """
        
        await target_conn.execute(text(query), values)
    
    async def _execute_update(
        self, 
        target_conn: Any, 
        sync_config: IncrementalSync, 
        change: Dict[str, Any]
    ):
        """Execute UPDATE operation."""
        
        # Build SET clause
        set_clauses = []
        values = []
        
        for column, value in change.items():
            if column not in sync_config.primary_key_columns:
                set_clauses.append(f"{column} = %s")
                values.append(value)
        
        # Build WHERE clause for primary key
        where_clauses = []
        for pk_column in sync_config.primary_key_columns:
            where_clauses.append(f"{pk_column} = %s")
            values.append(change[pk_column])
        
        query = f"""
        UPDATE {sync_config.target_table}
        SET {', '.join(set_clauses)}
        WHERE {' AND '.join(where_clauses)}
        """
        
        await target_conn.execute(text(query), values)
    
    async def _execute_delete(
        self, 
        target_conn: Any, 
        sync_config: IncrementalSync, 
        change: Dict[str, Any]
    ):
        """Execute DELETE operation."""
        
        # Build WHERE clause for primary key
        where_clauses = []
        values = []
        
        for pk_column in sync_config.primary_key_columns:
            where_clauses.append(f"{pk_column} = %s")
            values.append(change[pk_column])
        
        query = f"""
        DELETE FROM {sync_config.target_table}
        WHERE {' AND '.join(where_clauses)}
        """
        
        await target_conn.execute(text(query), values)
    
    async def _extract_log_based_changes(
        self, 
        source_conn: Any, 
        sync_config: IncrementalSync, 
        last_sync: datetime
    ) -> List[Dict[str, Any]]:
        """Extract changes using database transaction logs."""
        
        # Implementation would depend on specific database system
        # This is a placeholder for log-based change detection
        logger.warning("Log-based change detection not yet implemented")
        return []
    
    async def _update_sync_timestamp(
        self, 
        sync_config: IncrementalSync, 
        session: AsyncSession
    ):
        """Update the last sync timestamp."""
        
        # In a real implementation, this would update the sync history table
        sync_config.last_sync_timestamp = datetime.utcnow()
        logger.info(f"Updated sync timestamp for {sync_config.sync_id}")
