"""
Real-time migration monitoring service.
Tracks migration progress, performance, issues, and provides recommendations.
"""
from datetime import datetime, timedelta
from typing import List, Tuple
import random
from models.monitor_models import (
    MigrationStatus, HealthStatus, IssueType, IssueSeverity,
    ProgressMetrics, PerformanceMetrics, MigrationIssue,
    ResourceUtilization, LogEntry, MonitorSummary
)


class MigrationMonitor:
    """
    Service for monitoring real-time migration operations.
    Simulates realistic monitoring data based on migration state.
    """
    
    def __init__(self):
        """Initialize the migration monitor"""
        # Simulated migration states (in production, would query actual migration database)
        self.migrations = {}
        
    def monitor_migration(
        self,
        migration_id: str,
        include_metrics: bool = True,
        include_logs: bool = False
    ) -> Tuple[MonitorSummary, ProgressMetrics, PerformanceMetrics, 
               List[MigrationIssue], ResourceUtilization, List[LogEntry], List[str]]:
        """
        Monitor a migration operation and return current state.
        
        Args:
            migration_id: Unique identifier for the migration
            include_metrics: Whether to include performance metrics
            include_logs: Whether to include recent log entries
            
        Returns:
            Tuple of (summary, progress, performance, issues, resources, logs, recommendations)
        """
        # Get or create migration state
        if migration_id not in self.migrations:
            self.migrations[migration_id] = self._initialize_migration(migration_id)
            
        state = self.migrations[migration_id]
        
        # Update migration state
        self._update_migration_state(state)
        
        # Generate monitoring data
        summary = self._generate_summary(migration_id, state)
        progress = self._generate_progress(state)
        performance = self._generate_performance(state) if include_metrics else None
        issues = self._generate_issues(state)
        resources = self._generate_resource_utilization(state)
        logs = self._generate_logs(state) if include_logs else []
        recommendations = self._generate_recommendations(state, issues, performance)
        
        return summary, progress, performance, issues, resources, logs, recommendations
        
    def _initialize_migration(self, migration_id: str) -> dict:
        """Initialize a new migration state"""
        return {
            "migration_id": migration_id,
            "start_time": datetime.now() - timedelta(hours=2),
            "status": MigrationStatus.DATA_MIGRATION,
            "total_tables": 50,
            "completed_tables": 25,
            "failed_tables": 1,
            "total_rows": 10000000,
            "migrated_rows": 5000000,
            "failed_rows": 1000,
            "current_table": "orders",
            "rows_per_second": 2500.0,
            "cpu_usage": 65.0,
            "memory_usage": 8192.0,
            "issues": [],
            "health": HealthStatus.WARNING
        }
        
    def _update_migration_state(self, state: dict):
        """Update migration state to simulate progress"""
        # Simulate progress
        if state["status"] == MigrationStatus.DATA_MIGRATION:
            state["migrated_rows"] = min(
                state["migrated_rows"] + 50000,
                state["total_rows"]
            )
            state["completed_tables"] = min(
                int(state["migrated_rows"] / state["total_rows"] * state["total_tables"]),
                state["total_tables"]
            )
            
            # Check if migration is complete
            if state["migrated_rows"] >= state["total_rows"]:
                state["status"] = MigrationStatus.VALIDATION
                
        # Update health based on issues
        if state["failed_rows"] > 10000:
            state["health"] = HealthStatus.CRITICAL
        elif state["failed_tables"] > 0 or state["failed_rows"] > 0:
            state["health"] = HealthStatus.WARNING
        else:
            state["health"] = HealthStatus.HEALTHY
            
    def _generate_summary(self, migration_id: str, state: dict) -> MonitorSummary:
        """Generate monitoring summary"""
        current_time = datetime.now()
        elapsed = int((current_time - state["start_time"]).total_seconds())
        
        # Estimate total time based on progress
        progress_pct = (state["migrated_rows"] / state["total_rows"]) * 100
        estimated_total = int(elapsed / (progress_pct / 100)) if progress_pct > 0 else None
        
        return MonitorSummary(
            migration_id=migration_id,
            status=state["status"],
            health=state["health"],
            start_time=state["start_time"],
            current_time=current_time,
            elapsed_time_seconds=elapsed,
            estimated_total_time_seconds=estimated_total
        )
        
    def _generate_progress(self, state: dict) -> ProgressMetrics:
        """Generate progress metrics"""
        percentage = (state["migrated_rows"] / state["total_rows"]) * 100
        
        # Calculate estimated time remaining
        elapsed = (datetime.now() - state["start_time"]).total_seconds()
        if percentage > 0:
            total_estimated = elapsed / (percentage / 100)
            remaining = int(total_estimated - elapsed)
        else:
            remaining = None
            
        return ProgressMetrics(
            total_tables=state["total_tables"],
            completed_tables=state["completed_tables"],
            failed_tables=state["failed_tables"],
            total_rows=state["total_rows"],
            migrated_rows=state["migrated_rows"],
            failed_rows=state["failed_rows"],
            percentage_complete=round(percentage, 2),
            current_table=state["current_table"],
            estimated_time_remaining=remaining
        )
        
    def _generate_performance(self, state: dict) -> PerformanceMetrics:
        """Generate performance metrics"""
        # Simulate realistic performance metrics with some variance
        base_throughput = state["rows_per_second"]
        variance = random.uniform(0.9, 1.1)
        
        return PerformanceMetrics(
            rows_per_second=base_throughput * variance,
            avg_rows_per_second=base_throughput,
            peak_rows_per_second=base_throughput * 1.5,
            cpu_usage_percent=state["cpu_usage"] + random.uniform(-5, 5),
            memory_usage_mb=state["memory_usage"] + random.uniform(-500, 500),
            network_throughput_mbps=125.5 + random.uniform(-10, 10),
            source_connection_pool=10,
            target_connection_pool=10,
            error_rate=(state["failed_rows"] / state["migrated_rows"]) * 100 if state["migrated_rows"] > 0 else 0.0
        )
        
    def _generate_issues(self, state: dict) -> List[MigrationIssue]:
        """Generate list of migration issues"""
        issues = []
        
        # Add issues based on failures
        if state["failed_tables"] > 0:
            issues.append(MigrationIssue(
                issue_id="ISS-001",
                timestamp=datetime.now() - timedelta(minutes=30),
                type=IssueType.DATA_INTEGRITY,
                severity=IssueSeverity.HIGH,
                table_name="customers",
                description="Foreign key constraint violation during data migration",
                affected_rows=1000,
                resolution="Temporarily disable constraints, migrate data, then re-enable",
                resolved=True
            ))
            
        if state["failed_rows"] > 0:
            issues.append(MigrationIssue(
                issue_id="ISS-002",
                timestamp=datetime.now() - timedelta(minutes=5),
                type=IssueType.DATA_INTEGRITY,
                severity=IssueSeverity.MEDIUM,
                table_name=state["current_table"],
                description=f"Data type mismatch causing {state['failed_rows']} row failures",
                affected_rows=state["failed_rows"],
                resolution="Review data type mappings and transform data accordingly",
                resolved=False
            ))
            
        # Add performance warning if slow
        if state["cpu_usage"] > 80:
            issues.append(MigrationIssue(
                issue_id="ISS-003",
                timestamp=datetime.now() - timedelta(seconds=30),
                type=IssueType.PERFORMANCE,
                severity=IssueSeverity.MEDIUM,
                description="High CPU usage detected, migration may be slower than expected",
                resolution="Consider reducing concurrent threads or increasing resources",
                resolved=False
            ))
            
        return issues
        
    def _generate_resource_utilization(self, state: dict) -> ResourceUtilization:
        """Generate resource utilization metrics"""
        return ResourceUtilization(
            source_db_connections=10,
            target_db_connections=10,
            worker_threads=8,
            queue_depth=1500,
            temp_storage_mb=2048.5
        )
        
    def _generate_logs(self, state: dict) -> List[LogEntry]:
        """Generate recent log entries"""
        return [
            LogEntry(
                timestamp=datetime.now() - timedelta(seconds=10),
                level="INFO",
                message=f"Migrating table '{state['current_table']}' - {state['migrated_rows']:,} rows completed",
                context={"table": state["current_table"], "progress": f"{(state['migrated_rows']/state['total_rows'])*100:.1f}%"}
            ),
            LogEntry(
                timestamp=datetime.now() - timedelta(seconds=30),
                level="WARNING",
                message=f"Row migration failed for {state['failed_rows']} rows due to data type mismatch",
                context={"failed_rows": state["failed_rows"], "table": state["current_table"]}
            ),
            LogEntry(
                timestamp=datetime.now() - timedelta(minutes=1),
                level="INFO",
                message=f"Completed migration of table 'products' - 250,000 rows transferred",
                context={"table": "products", "rows": 250000}
            )
        ]
        
    def _generate_recommendations(
        self, 
        state: dict, 
        issues: List[MigrationIssue],
        performance: PerformanceMetrics
    ) -> List[str]:
        """Generate recommendations based on current state"""
        recommendations = []
        
        # Performance recommendations
        if performance and performance.rows_per_second < 1000:
            recommendations.append(
                "Consider increasing parallelism or optimizing batch sizes to improve throughput"
            )
            
        if performance and performance.cpu_usage_percent > 80:
            recommendations.append(
                "High CPU usage detected. Consider scaling up resources or reducing concurrent operations"
            )
            
        # Issue-based recommendations
        unresolved_critical = [i for i in issues if i.severity == IssueSeverity.CRITICAL and not i.resolved]
        if unresolved_critical:
            recommendations.append(
                "Critical issues detected. Recommend pausing migration to investigate and resolve"
            )
            
        # Data integrity recommendations
        if state["failed_rows"] > state["total_rows"] * 0.01:  # More than 1% failure
            recommendations.append(
                "High data failure rate detected. Review data type mappings and validation rules"
            )
            
        # Progress recommendations
        percentage = (state["migrated_rows"] / state["total_rows"]) * 100
        if percentage > 90:
            recommendations.append(
                "Migration is nearly complete. Prepare for validation phase and final cutover"
            )
            
        if not recommendations:
            recommendations.append("Migration is progressing well. Continue monitoring for issues")
            
        return recommendations


def monitor_migration(
    migration_id: str,
    include_metrics: bool = True,
    include_logs: bool = False
) -> Tuple[MonitorSummary, ProgressMetrics, PerformanceMetrics,
           List[MigrationIssue], ResourceUtilization, List[LogEntry], List[str]]:
    """
    Monitor a migration operation.
    
    Args:
        migration_id: Unique identifier for the migration
        include_metrics: Whether to include performance metrics
        include_logs: Whether to include recent log entries
        
    Returns:
        Tuple of monitoring data components
    """
    monitor = MigrationMonitor()
    return monitor.monitor_migration(migration_id, include_metrics, include_logs)
