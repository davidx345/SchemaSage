"""
Monitoring Engine - Core monitoring and alerting functionality
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.monitoring import (
    MonitoringRule, Alert, AlertSeverity, AlertStatus, MetricType, NotificationChannel
)
from ...core.database import DatabaseManager
from ...utils.logging import get_logger
from ...utils.exceptions import MonitoringError
from .notification_service import NotificationService

logger = get_logger(__name__)

class MonitoringEngine:
    """Real-time monitoring and alerting engine."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.active_rules: Dict[str, MonitoringRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.notification_service = NotificationService()
    
    async def start_monitoring(self, workspace_id: str, session: AsyncSession):
        """Start monitoring for a workspace."""
        
        try:
            # Load monitoring rules
            rules = await self._load_monitoring_rules(workspace_id, session)
            
            # Start monitoring tasks for each rule
            for rule in rules:
                if rule.is_active:
                    self.active_rules[rule.rule_id] = rule
                    task = asyncio.create_task(
                        self._monitor_rule(rule, session)
                    )
                    self.monitoring_tasks[rule.rule_id] = task
            
            logger.info(f"Started monitoring {len(rules)} rules for workspace {workspace_id}")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            raise MonitoringError(f"Failed to start monitoring: {e}")
    
    async def stop_monitoring(self, workspace_id: str):
        """Stop monitoring for a workspace."""
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        self.monitoring_tasks.clear()
        self.active_rules.clear()
        
        logger.info(f"Stopped monitoring for workspace {workspace_id}")
    
    async def _load_monitoring_rules(
        self, 
        workspace_id: str, 
        session: AsyncSession
    ) -> List[MonitoringRule]:
        """Load monitoring rules from database."""
        
        # In a real implementation, this would query the database
        # For now, return sample rules
        return [
            MonitoringRule(
                workspace_id=workspace_id,
                name="High Query Execution Time",
                description="Alert when query execution time exceeds threshold",
                metric_type=MetricType.PERFORMANCE,
                metric_name="average_query_time",
                operator=">",
                threshold_value=1000.0,  # milliseconds
                evaluation_window_minutes=5,
                alert_severity=AlertSeverity.HIGH,
                notification_channels=[NotificationChannel.EMAIL],
                created_by="system"
            ),
            MonitoringRule(
                workspace_id=workspace_id,
                name="Low Cache Hit Ratio",
                description="Alert when cache hit ratio drops below threshold",
                metric_type=MetricType.PERFORMANCE,
                metric_name="cache_hit_ratio",
                operator="<",
                threshold_value=85.0,  # percentage
                evaluation_window_minutes=10,
                alert_severity=AlertSeverity.MEDIUM,
                notification_channels=[NotificationChannel.EMAIL],
                created_by="system"
            )
        ]
    
    async def _monitor_rule(self, rule: MonitoringRule, session: AsyncSession):
        """Monitor a specific rule continuously."""
        
        consecutive_violations = 0
        last_alert_time = None
        
        while True:
            try:
                # Evaluate the rule
                current_value = await self._evaluate_rule(rule, session)
                
                # Check if threshold is violated
                violation = self._check_threshold_violation(rule, current_value)
                
                if violation:
                    consecutive_violations += 1
                    
                    # Check if we should trigger an alert
                    if consecutive_violations >= rule.consecutive_violations:
                        # Check cooldown period
                        if (not last_alert_time or 
                            datetime.utcnow() - last_alert_time > timedelta(minutes=rule.cooldown_minutes)):
                            
                            await self._trigger_alert(rule, current_value, session)
                            last_alert_time = datetime.utcnow()
                else:
                    consecutive_violations = 0
                    
                    # Auto-resolve alerts if enabled
                    if rule.auto_resolve:
                        await self._auto_resolve_alerts(rule, session)
                
                # Update rule evaluation timestamp
                rule.last_evaluated = datetime.utcnow()
                
                # Wait for next evaluation cycle
                await asyncio.sleep(rule.evaluation_window_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info(f"Monitoring cancelled for rule {rule.rule_id}")
                break
            except Exception as e:
                logger.error(f"Error monitoring rule {rule.rule_id}: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _evaluate_rule(self, rule: MonitoringRule, session: AsyncSession) -> float:
        """Evaluate a monitoring rule and return current value."""
        
        if rule.custom_sql:
            # Execute custom SQL
            return await self._execute_custom_rule(rule, session)
        else:
            # Use built-in metric collection
            return await self._collect_builtin_metric(rule, session)
    
    async def _execute_custom_rule(self, rule: MonitoringRule, session: AsyncSession) -> float:
        """Execute custom SQL rule."""
        
        try:
            connection = await self.db_manager.get_connection(rule.connection_id)
            
            async with connection.execute(text(rule.custom_sql)) as result:
                row = await result.fetchone()
                
                if row and row[0] is not None:
                    return float(row[0])
                else:
                    return 0.0
        
        except Exception as e:
            logger.error(f"Error executing custom rule {rule.rule_id}: {e}")
            return 0.0
    
    async def _collect_builtin_metric(self, rule: MonitoringRule, session: AsyncSession) -> float:
        """Collect built-in metric value."""
        
        # This would integrate with the performance monitoring service
        # For now, return mock values based on metric name
        
        if rule.metric_name == "average_query_time":
            return 500.0  # Mock value in milliseconds
        elif rule.metric_name == "cache_hit_ratio":
            return 92.5   # Mock value in percentage
        elif rule.metric_name == "active_connections":
            return 45     # Mock value
        elif rule.metric_name == "database_size_mb":
            return 1024.0 # Mock value in MB
        else:
            return 0.0
    
    def _check_threshold_violation(self, rule: MonitoringRule, current_value: float) -> bool:
        """Check if current value violates the threshold."""
        
        threshold = float(rule.threshold_value)
        
        if rule.operator == ">":
            return current_value > threshold
        elif rule.operator == "<":
            return current_value < threshold
        elif rule.operator == ">=":
            return current_value >= threshold
        elif rule.operator == "<=":
            return current_value <= threshold
        elif rule.operator == "==":
            return current_value == threshold
        elif rule.operator == "!=":
            return current_value != threshold
        else:
            return False
    
    async def _trigger_alert(
        self, 
        rule: MonitoringRule, 
        current_value: float, 
        session: AsyncSession
    ):
        """Trigger an alert for a violated rule."""
        
        alert = Alert(
            rule_id=rule.rule_id,
            workspace_id=rule.workspace_id,
            connection_id=rule.connection_id,
            title=f"Monitoring Alert: {rule.name}",
            description=f"{rule.description}. Current value: {current_value}, Threshold: {rule.threshold_value}",
            severity=rule.alert_severity,
            trigger_value=current_value,
            threshold_value=rule.threshold_value,
            evaluation_window=timedelta(minutes=rule.evaluation_window_minutes)
        )
        
        # Store alert
        self.active_alerts[alert.alert_id] = alert
        
        # Send notifications
        await self.notification_service.send_alert_notifications(alert, rule)
        
        # Log alert
        logger.warning(f"Alert triggered: {alert.title} (ID: {alert.alert_id})")
    
    async def _auto_resolve_alerts(self, rule: MonitoringRule, session: AsyncSession):
        """Auto-resolve alerts for a rule when condition is no longer violated."""
        
        # Find active alerts for this rule
        rule_alerts = [
            alert for alert in self.active_alerts.values()
            if alert.rule_id == rule.rule_id and alert.status == AlertStatus.ACTIVE
        ]
        
        for alert in rule_alerts:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.auto_resolved = True
            alert.resolution_notes = "Automatically resolved - condition no longer violated"
            
            # Send resolution notification
            await self.notification_service.send_resolution_notification(alert, rule)
            
            logger.info(f"Auto-resolved alert: {alert.alert_id}")
