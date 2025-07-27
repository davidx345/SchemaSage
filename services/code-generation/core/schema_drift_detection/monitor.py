"""
Schema monitoring for real-time drift detection
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime, timedelta
import uuid

from models.schemas import SchemaResponse, TableInfo, ColumnInfo

from .models import (
    SchemaSnapshot, SchemaChange, DriftAlert, MonitoringConfig,
    DatabaseConnection, ChangeType, ChangeSeverity, AlertChannel
)

logger = logging.getLogger(__name__)


class SchemaMonitor:
    """Main class for monitoring schema changes in real-time"""
    
    def __init__(self, database_config: DatabaseConnection, config: MonitoringConfig = None):
        """
        Initialize schema monitor
        
        Args:
            database_config: Database connection configuration
            config: Monitoring configuration
        """
        self.database_config = database_config
        self.config = config or MonitoringConfig()
        self.snapshots: List[SchemaSnapshot] = []
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.alert_callbacks: List[Callable[[DriftAlert], None]] = []
        
    async def start_monitoring(self):
        """Start the monitoring process"""
        if self.is_monitoring:
            logger.warning("Monitoring is already running")
            return
            
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Schema monitoring started")
        
    async def stop_monitoring(self):
        """Stop the monitoring process"""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Schema monitoring stopped")
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.is_monitoring:
                try:
                    # Capture current schema
                    current_schema = await self._capture_schema()
                    current_snapshot = SchemaSnapshot(
                        snapshot_id=str(uuid.uuid4()),
                        schema_hash=self._calculate_schema_hash(current_schema),
                        schema=current_schema
                    )
                    
                    # Compare with previous snapshot if available
                    if self.snapshots:
                        previous_snapshot = self.snapshots[-1]
                        changes = self._detect_changes(previous_snapshot, current_snapshot)
                        
                        if changes:
                            logger.info(f"Detected {len(changes)} schema changes")
                            await self._process_changes(changes)
                    
                    # Store snapshot
                    self.snapshots.append(current_snapshot)
                    
                    # Cleanup old snapshots
                    self._cleanup_snapshots()
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                
                # Wait for next check
                await asyncio.sleep(self.config.check_interval)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
            raise
    
    async def _capture_schema(self) -> SchemaResponse:
        """Capture current schema from database"""
        # This would implement actual database connection and schema extraction
        # For now, return a mock schema
        logger.debug("Capturing schema from database")
        
        # TODO: Implement actual schema capture based on database type
        return SchemaResponse(
            tables=[],
            relationships=[],
            metadata={
                "captured_at": datetime.now().isoformat(),
                "database": self.database_config.database
            }
        )
    
    def _calculate_schema_hash(self, schema: SchemaResponse) -> str:
        """Calculate a hash of the schema for change detection"""
        # Convert schema to a stable string representation
        schema_dict = {
            'tables': [
                {
                    'name': table.name,
                    'columns': [
                        {
                            'name': col.name,
                            'type': col.type,
                            'nullable': col.nullable,
                            'is_primary_key': col.is_primary_key,
                            'unique': getattr(col, 'unique', False),
                            'default': col.default
                        }
                        for col in table.columns
                    ],
                    'primary_keys': table.primary_keys or [],
                    'foreign_keys': table.foreign_keys or [],
                    'indexes': table.indexes or []
                }
                for table in schema.tables
            ],
            'relationships': [
                {
                    'source_table': rel.source_table,
                    'source_column': rel.source_column,
                    'target_table': rel.target_table,
                    'target_column': rel.target_column,
                    'type': rel.type
                }
                for rel in (schema.relationships or [])
            ]
        }
        
        # Sort to ensure consistent ordering
        schema_str = json.dumps(schema_dict, sort_keys=True)
        
        # Calculate hash
        return hashlib.sha256(schema_str.encode()).hexdigest()
    
    def _detect_changes(
        self, 
        old_snapshot: SchemaSnapshot, 
        new_snapshot: SchemaSnapshot
    ) -> List[SchemaChange]:
        """Detect changes between two schema snapshots"""
        
        if old_snapshot.schema_hash == new_snapshot.schema_hash:
            return []  # No changes
            
        changes = []
        old_schema = old_snapshot.schema
        new_schema = new_snapshot.schema
        
        # Detect table changes
        changes.extend(self._detect_table_changes(old_schema, new_schema))
        
        # Detect column changes
        changes.extend(self._detect_column_changes(old_schema, new_schema))
        
        # Detect relationship changes
        changes.extend(self._detect_relationship_changes(old_schema, new_schema))
        
        # Filter out ignored changes
        changes = [
            change for change in changes
            if not self.config.should_ignore_change(change.change_type)
        ]
        
        return changes
    
    def _detect_table_changes(
        self, 
        old_schema: SchemaResponse, 
        new_schema: SchemaResponse
    ) -> List[SchemaChange]:
        """Detect table-level changes"""
        
        changes = []
        old_tables = {table.name: table for table in old_schema.tables}
        new_tables = {table.name: table for table in new_schema.tables}
        
        # Detect added tables
        for table_name in new_tables.keys() - old_tables.keys():
            if self.config.should_monitor_table(table_name):
                changes.append(SchemaChange(
                    change_id=str(uuid.uuid4()),
                    change_type=ChangeType.TABLE_ADDED,
                    severity=ChangeSeverity.MEDIUM,
                    object_name=table_name,
                    table_name=table_name,
                    details={
                        'table': new_tables[table_name].dict(),
                        'column_count': len(new_tables[table_name].columns)
                    }
                ))
        
        # Detect removed tables
        for table_name in old_tables.keys() - new_tables.keys():
            if self.config.should_monitor_table(table_name):
                changes.append(SchemaChange(
                    change_id=str(uuid.uuid4()),
                    change_type=ChangeType.TABLE_REMOVED,
                    severity=ChangeSeverity.CRITICAL,
                    object_name=table_name,
                    table_name=table_name,
                    details={
                        'table': old_tables[table_name].dict(),
                        'column_count': len(old_tables[table_name].columns)
                    }
                ))
        
        return changes
    
    def _detect_column_changes(
        self, 
        old_schema: SchemaResponse, 
        new_schema: SchemaResponse
    ) -> List[SchemaChange]:
        """Detect column-level changes"""
        
        changes = []
        old_tables = {table.name: table for table in old_schema.tables}
        new_tables = {table.name: table for table in new_schema.tables}
        
        # Check tables that exist in both schemas
        for table_name in old_tables.keys() & new_tables.keys():
            if not self.config.should_monitor_table(table_name):
                continue
                
            old_table = old_tables[table_name]
            new_table = new_tables[table_name]
            
            old_columns = {col.name: col for col in old_table.columns}
            new_columns = {col.name: col for col in new_table.columns}
            
            # Detect added columns
            for col_name in new_columns.keys() - old_columns.keys():
                changes.append(SchemaChange(
                    change_id=str(uuid.uuid4()),
                    change_type=ChangeType.COLUMN_ADDED,
                    severity=ChangeSeverity.LOW,
                    object_name=f"{table_name}.{col_name}",
                    table_name=table_name,
                    column_name=col_name,
                    details={
                        'column': new_columns[col_name].dict()
                    }
                ))
            
            # Detect removed columns
            for col_name in old_columns.keys() - new_columns.keys():
                changes.append(SchemaChange(
                    change_id=str(uuid.uuid4()),
                    change_type=ChangeType.COLUMN_REMOVED,
                    severity=ChangeSeverity.HIGH,
                    object_name=f"{table_name}.{col_name}",
                    table_name=table_name,
                    column_name=col_name,
                    details={
                        'column': old_columns[col_name].dict()
                    }
                ))
            
            # Detect modified columns
            for col_name in old_columns.keys() & new_columns.keys():
                old_col = old_columns[col_name]
                new_col = new_columns[col_name]
                
                if self._columns_differ(old_col, new_col):
                    changes.append(SchemaChange(
                        change_id=str(uuid.uuid4()),
                        change_type=ChangeType.COLUMN_MODIFIED,
                        severity=self._determine_column_change_severity(old_col, new_col),
                        object_name=f"{table_name}.{col_name}",
                        table_name=table_name,
                        column_name=col_name,
                        old_value=old_col.dict(),
                        new_value=new_col.dict(),
                        details={
                            'changes': self._get_column_differences(old_col, new_col)
                        }
                    ))
        
        return changes
    
    def _detect_relationship_changes(
        self, 
        old_schema: SchemaResponse, 
        new_schema: SchemaResponse
    ) -> List[SchemaChange]:
        """Detect relationship changes"""
        
        changes = []
        old_relationships = set()
        new_relationships = set()
        
        # Convert relationships to comparable tuples
        for rel in (old_schema.relationships or []):
            old_relationships.add((
                rel.source_table, rel.source_column,
                rel.target_table, rel.target_column, rel.type
            ))
        
        for rel in (new_schema.relationships or []):
            new_relationships.add((
                rel.source_table, rel.source_column,
                rel.target_table, rel.target_column, rel.type
            ))
        
        # Detect added relationships
        for rel_tuple in new_relationships - old_relationships:
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.FOREIGN_KEY_ADDED,
                severity=ChangeSeverity.MEDIUM,
                object_name=f"{rel_tuple[0]}.{rel_tuple[1]} -> {rel_tuple[2]}.{rel_tuple[3]}",
                details={
                    'relationship': {
                        'source_table': rel_tuple[0],
                        'source_column': rel_tuple[1],
                        'target_table': rel_tuple[2],
                        'target_column': rel_tuple[3],
                        'type': rel_tuple[4]
                    }
                }
            ))
        
        # Detect removed relationships
        for rel_tuple in old_relationships - new_relationships:
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.FOREIGN_KEY_REMOVED,
                severity=ChangeSeverity.HIGH,
                object_name=f"{rel_tuple[0]}.{rel_tuple[1]} -> {rel_tuple[2]}.{rel_tuple[3]}",
                details={
                    'relationship': {
                        'source_table': rel_tuple[0],
                        'source_column': rel_tuple[1],
                        'target_table': rel_tuple[2],
                        'target_column': rel_tuple[3],
                        'type': rel_tuple[4]
                    }
                }
            ))
        
        return changes
    
    def _columns_differ(self, old_col: ColumnInfo, new_col: ColumnInfo) -> bool:
        """Check if two columns are different"""
        return (
            old_col.type != new_col.type or
            old_col.nullable != new_col.nullable or
            old_col.is_primary_key != new_col.is_primary_key or
            old_col.default != new_col.default or
            getattr(old_col, 'unique', False) != getattr(new_col, 'unique', False)
        )
    
    def _determine_column_change_severity(
        self, 
        old_col: ColumnInfo, 
        new_col: ColumnInfo
    ) -> ChangeSeverity:
        """Determine severity of column changes"""
        
        # Type changes are usually critical
        if old_col.type != new_col.type:
            return ChangeSeverity.CRITICAL
        
        # Nullability changes can be breaking
        if old_col.nullable != new_col.nullable:
            if old_col.nullable and not new_col.nullable:
                return ChangeSeverity.HIGH  # Making non-nullable can break existing data
            else:
                return ChangeSeverity.MEDIUM
        
        # Primary key changes are critical
        if old_col.is_primary_key != new_col.is_primary_key:
            return ChangeSeverity.CRITICAL
        
        # Default value changes are usually low impact
        if old_col.default != new_col.default:
            return ChangeSeverity.LOW
        
        # Other changes are medium
        return ChangeSeverity.MEDIUM
    
    def _get_column_differences(
        self, 
        old_col: ColumnInfo, 
        new_col: ColumnInfo
    ) -> Dict[str, Any]:
        """Get specific differences between columns"""
        
        differences = {}
        
        if old_col.type != new_col.type:
            differences['type'] = {'old': old_col.type, 'new': new_col.type}
        
        if old_col.nullable != new_col.nullable:
            differences['nullable'] = {'old': old_col.nullable, 'new': new_col.nullable}
        
        if old_col.is_primary_key != new_col.is_primary_key:
            differences['is_primary_key'] = {'old': old_col.is_primary_key, 'new': new_col.is_primary_key}
        
        if old_col.default != new_col.default:
            differences['default'] = {'old': old_col.default, 'new': new_col.default}
        
        old_unique = getattr(old_col, 'unique', False)
        new_unique = getattr(new_col, 'unique', False)
        if old_unique != new_unique:
            differences['unique'] = {'old': old_unique, 'new': new_unique}
        
        return differences
    
    async def _process_changes(self, changes: List[SchemaChange]):
        """Process detected changes and trigger alerts if necessary"""
        
        # Group changes by severity
        severity_counts = {}
        for severity in ChangeSeverity:
            severity_counts[severity] = 0
        
        for change in changes:
            severity_counts[change.severity] += 1
        
        # Check if alert should be triggered
        should_alert = False
        alert_severity = ChangeSeverity.LOW
        
        for severity, count in severity_counts.items():
            threshold = self.config.severity_thresholds.get(severity.value, float('inf'))
            if count >= threshold:
                should_alert = True
                alert_severity = severity
                break
        
        if should_alert:
            alert = DriftAlert(
                alert_id=str(uuid.uuid4()),
                changes=changes,
                severity=alert_severity,
                message=f"Schema drift detected: {len(changes)} changes",
                channels=self.config.alert_channels
            )
            
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: DriftAlert):
        """Send alert through configured channels"""
        
        logger.warning(f"Schema drift alert: {alert.message}")
        
        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def add_alert_callback(self, callback: Callable[[DriftAlert], None]):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[DriftAlert], None]):
        """Remove callback function"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def _cleanup_snapshots(self):
        """Clean up old snapshots based on retention policy"""
        
        # Keep only max_snapshots
        if len(self.snapshots) > self.config.max_snapshots:
            self.snapshots = self.snapshots[-self.config.max_snapshots:]
        
        # Remove snapshots older than retention period
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        self.snapshots = [
            snapshot for snapshot in self.snapshots
            if snapshot.captured_at > cutoff_date
        ]
    
    def get_latest_snapshot(self) -> Optional[SchemaSnapshot]:
        """Get the most recent schema snapshot"""
        return self.snapshots[-1] if self.snapshots else None
    
    def get_snapshot_history(self, limit: int = 10) -> List[SchemaSnapshot]:
        """Get recent snapshot history"""
        return self.snapshots[-limit:] if self.snapshots else []
