"""
Schema Drift Detection Module

This module provides comprehensive schema drift detection capabilities including
real-time monitoring, change comparison, alerting, and impact analysis.
"""

from .models import (
    ChangeType,
    ChangeSeverity,
    AlertChannel,
    SchemaChange,
    SchemaSnapshot,
    DriftAlert,
    MonitoringConfig,
    ImpactAnalysis,
    DatabaseConnection,
    ComparisonResult
)

from .monitor import SchemaMonitor
from .comparator import SchemaComparator
from .alerting import AlertManager, AlertFilter
from .impact_analyzer import ImpactAnalyzer

__all__ = [
    # Enums
    'ChangeType',
    'ChangeSeverity', 
    'AlertChannel',
    
    # Data Models
    'SchemaChange',
    'SchemaSnapshot',
    'DriftAlert',
    'MonitoringConfig',
    'ImpactAnalysis',
    'DatabaseConnection',
    'ComparisonResult',
    
    # Core Classes
    'SchemaMonitor',
    'SchemaComparator',
    'AlertManager',
    'AlertFilter',
    'ImpactAnalyzer',
    'SchemaDriftDetector'
]


class SchemaDriftDetector:
    """
    Main orchestrator class for schema drift detection
    
    Combines monitoring, comparison, alerting, and impact analysis
    into a unified drift detection system.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize schema drift detector
        
        Args:
            config: Global configuration dictionary
        """
        self.config = config or {}
        self.monitors = {}
        self.comparator = SchemaComparator()
        self.alert_manager = AlertManager(self.config.get('alerting', {}))
        self.impact_analyzer = ImpactAnalyzer(self.config.get('applications', {}))
        self.is_running = False
    
    def add_database(
        self, 
        database_name: str, 
        connection_config: DatabaseConnection,
        monitoring_config: MonitoringConfig = None
    ):
        """
        Add database for monitoring
        
        Args:
            database_name: Unique identifier for database
            connection_config: Database connection configuration
            monitoring_config: Monitoring-specific configuration
        """
        monitoring_config = monitoring_config or MonitoringConfig()
        
        monitor = SchemaMonitor(connection_config, monitoring_config)
        monitor.add_alert_callback(self._handle_drift_alert)
        
        self.monitors[database_name] = monitor
    
    def remove_database(self, database_name: str):
        """Remove database from monitoring"""
        if database_name in self.monitors:
            monitor = self.monitors[database_name]
            if monitor.is_monitoring:
                import asyncio
                asyncio.create_task(monitor.stop_monitoring())
            del self.monitors[database_name]
    
    async def start_monitoring(self, database_name: str = None):
        """
        Start monitoring for specified database or all databases
        
        Args:
            database_name: Specific database to monitor, or None for all
        """
        if database_name:
            if database_name in self.monitors:
                await self.monitors[database_name].start_monitoring()
        else:
            for monitor in self.monitors.values():
                await monitor.start_monitoring()
        
        self.is_running = True
    
    async def stop_monitoring(self, database_name: str = None):
        """
        Stop monitoring for specified database or all databases
        
        Args:
            database_name: Specific database to stop, or None for all
        """
        if database_name:
            if database_name in self.monitors:
                await self.monitors[database_name].stop_monitoring()
        else:
            for monitor in self.monitors.values():
                await monitor.stop_monitoring()
            self.is_running = False
    
    async def compare_schemas(
        self,
        database_name: str,
        old_schema_id: str = None,
        new_schema_id: str = None
    ) -> ComparisonResult:
        """
        Compare two schema snapshots
        
        Args:
            database_name: Database to compare
            old_schema_id: ID of older snapshot (None for previous)
            new_schema_id: ID of newer snapshot (None for latest)
            
        Returns:
            Detailed comparison result
        """
        if database_name not in self.monitors:
            raise ValueError(f"Database '{database_name}' not found")
        
        monitor = self.monitors[database_name]
        snapshots = monitor.get_snapshot_history()
        
        if len(snapshots) < 2:
            raise ValueError("Need at least 2 snapshots to compare")
        
        # Get snapshots to compare
        if new_schema_id is None:
            new_snapshot = snapshots[-1]
        else:
            new_snapshot = next((s for s in snapshots if s.snapshot_id == new_schema_id), None)
            if not new_snapshot:
                raise ValueError(f"Snapshot '{new_schema_id}' not found")
        
        if old_schema_id is None:
            # Find previous snapshot
            snapshot_index = next(i for i, s in enumerate(snapshots) if s.snapshot_id == new_snapshot.snapshot_id)
            if snapshot_index == 0:
                raise ValueError("No previous snapshot available")
            old_snapshot = snapshots[snapshot_index - 1]
        else:
            old_snapshot = next((s for s in snapshots if s.snapshot_id == old_schema_id), None)
            if not old_snapshot:
                raise ValueError(f"Snapshot '{old_schema_id}' not found")
        
        # Perform comparison
        result = self.comparator.compare_schemas(
            old_snapshot.schema,
            new_snapshot.schema,
            database_name
        )
        
        return result
    
    async def analyze_impact(
        self,
        database_name: str,
        changes: list = None,
        schema_before = None,
        schema_after = None
    ) -> dict:
        """
        Analyze impact of schema changes
        
        Args:
            database_name: Database name
            changes: List of changes to analyze
            schema_before: Schema before changes
            schema_after: Schema after changes
            
        Returns:
            Impact analysis results
        """
        if changes is None:
            # Get recent changes
            comparison = await self.compare_schemas(database_name)
            changes = comparison.changes
        
        impact_analyses = self.impact_analyzer.analyze_changes(
            changes, schema_before, schema_after
        )
        
        return self.impact_analyzer.generate_impact_report(changes, impact_analyses)
    
    def _handle_drift_alert(self, alert: DriftAlert):
        """Handle drift alert from monitor"""
        import asyncio
        asyncio.create_task(self.alert_manager.send_alert(alert))
    
    def get_monitoring_status(self) -> dict:
        """Get status of all monitors"""
        status = {
            'is_running': self.is_running,
            'databases': {}
        }
        
        for db_name, monitor in self.monitors.items():
            status['databases'][db_name] = {
                'is_monitoring': monitor.is_monitoring,
                'latest_snapshot': monitor.get_latest_snapshot().to_dict() if monitor.get_latest_snapshot() else None,
                'snapshot_count': len(monitor.get_snapshot_history())
            }
        
        return status
    
    def add_alert_handler(self, handler):
        """Add custom alert handler"""
        self.alert_manager.add_custom_handler(handler)
    
    def configure_alerts(self, alert_config: dict):
        """Configure alerting settings"""
        self.alert_manager.config.update(alert_config)
