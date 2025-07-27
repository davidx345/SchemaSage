"""
Performance monitoring module initialization
"""

from .models import (
    MetricType,
    AlertLevel,
    PerformanceMetric,
    PerformanceAlert,
    SystemSnapshot,
    OperationStats,
    ActiveOperation,
    MetricStatistics,
    SystemTrend,
    PerformanceReport,
    ProfileResult,
    DEFAULT_ALERT_THRESHOLDS,
    create_metric,
    create_alert,
    is_metric_above_threshold
)

from .metrics_collector import (
    MetricsCollector,
    OperationTracker,
    BatchMetricsCollector,
    MemoryEfficientCollector
)

from .system_monitor import (
    SystemMonitor,
    ResourceAlertMonitor
)

from .alerting import (
    AlertManager,
    ThresholdManager,
    AlertNotifier,
    AlertAggregator,
    log_alert_handler,
    console_alert_handler,
    file_alert_handler
)

from .profiler import (
    PerformanceProfiler,
    LineProfiler,
    MemoryProfiler,
    CombinedProfiler,
    profile_performance,
    profile_memory
)

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import functools
import asyncio

logger = logging.getLogger(__name__)

__all__ = [
    # Models and types
    "MetricType",
    "AlertLevel", 
    "PerformanceMetric",
    "PerformanceAlert",
    "SystemSnapshot",
    "OperationStats",
    "ActiveOperation",
    "MetricStatistics",
    "SystemTrend",
    "PerformanceReport",
    "ProfileResult",
    "DEFAULT_ALERT_THRESHOLDS",
    
    # Utility functions
    "create_metric",
    "create_alert",
    "is_metric_above_threshold",
    
    # Core classes
    "MetricsCollector",
    "OperationTracker",
    "BatchMetricsCollector",
    "MemoryEfficientCollector",
    "SystemMonitor",
    "ResourceAlertMonitor",
    "AlertManager",
    "ThresholdManager",
    "AlertNotifier",
    "AlertAggregator",
    "PerformanceProfiler",
    "LineProfiler", 
    "MemoryProfiler",
    "CombinedProfiler",
    
    # Alert handlers
    "log_alert_handler",
    "console_alert_handler",
    "file_alert_handler",
    
    # Decorators
    "profile_performance",
    "profile_memory",
    
    # Main service class
    "PerformanceMonitorService"
]


class PerformanceMonitorService:
    """
    Main performance monitoring service that orchestrates all components
    """
    
    def __init__(
        self,
        alert_thresholds: Optional[Dict[MetricType, float]] = None,
        retention_hours: int = 24,
        system_monitoring_interval: int = 60
    ):
        # Initialize core components
        self.metrics_collector = MetricsCollector(retention_hours=retention_hours)
        self.operation_tracker = OperationTracker(self.metrics_collector)
        self.system_monitor = SystemMonitor(self.metrics_collector, system_monitoring_interval)
        self.alert_manager = AlertManager(alert_thresholds)
        self.threshold_manager = ThresholdManager()
        self.alert_notifier = AlertNotifier()
        self.profiler = CombinedProfiler()
        
        # Resource alert monitor
        self.resource_alert_monitor = ResourceAlertMonitor(self.system_monitor)
        
        # Service state
        self.is_running = False
        
        # Setup default alert handlers
        self._setup_default_alert_handlers()
    
    async def start(self):
        """Start the performance monitoring service"""
        if self.is_running:
            logger.warning("Performance monitoring already running")
            return
        
        self.is_running = True
        
        # Start system monitoring
        self.system_monitor.start_monitoring()
        
        # Register alert handler for metric checking
        self.alert_manager.register_alert_handler(
            AlertLevel.WARNING,
            self._handle_metric_alert
        )
        self.alert_manager.register_alert_handler(
            AlertLevel.ERROR,
            self._handle_metric_alert
        )
        self.alert_manager.register_alert_handler(
            AlertLevel.CRITICAL,
            self._handle_metric_alert
        )
        
        logger.info("Performance monitoring service started")
    
    async def stop(self):
        """Stop the performance monitoring service"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop system monitoring
        self.system_monitor.stop_monitoring()
        
        logger.info("Performance monitoring service stopped")
    
    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> PerformanceMetric:
        """
        Record a performance metric
        
        Args:
            metric_type: Type of metric
            value: Metric value
            context: Additional context data
            tags: Metric tags for filtering
            
        Returns:
            Created performance metric
        """
        metric = self.metrics_collector.record_metric(metric_type, value, context, tags)
        
        # Check for alerts
        alert = self.alert_manager.check_metric_alert(metric)
        if alert:
            self.alert_notifier.notify(alert)
        
        return metric
    
    def track_operation(self, operation_name: str, **context):
        """
        Context manager to track operation performance
        
        Args:
            operation_name: Name of the operation
            **context: Additional context data
            
        Returns:
            Context manager for operation tracking
        """
        return self.operation_tracker.track_operation(operation_name, **context)
    
    def track_function(self, operation_name: Optional[str] = None, **tracking_context):
        """
        Decorator to track function performance
        
        Args:
            operation_name: Custom operation name
            **tracking_context: Additional context data
            
        Returns:
            Decorator function
        """
        return self.operation_tracker.track_function(operation_name, **tracking_context)
    
    def profile_code(
        self,
        profile_name: str,
        target_function: Optional[Callable] = None,
        include_lines: bool = False,
        include_memory: bool = True
    ):
        """
        Context manager for comprehensive code profiling
        
        Args:
            profile_name: Name for the profile
            target_function: Function for line profiling
            include_lines: Whether to include line profiling
            include_memory: Whether to include memory profiling
            
        Returns:
            Context manager for profiling
        """
        return self.profiler.profile_all(profile_name, target_function, include_lines, include_memory)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        health = self.system_monitor.get_system_health()
        
        # Add alert information
        recent_alerts = self.alert_manager.get_alerts(time_range=timedelta(hours=1))
        health['recent_alerts'] = len(recent_alerts)
        health['critical_alerts'] = len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL])
        
        # Add active operations
        health['active_operations'] = len(self.operation_tracker.get_active_operations())
        
        return health
    
    def generate_performance_report(
        self,
        time_range: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Args:
            time_range: Time range for the report
            
        Returns:
            Performance report dictionary
        """
        time_range = time_range or timedelta(hours=1)
        
        # Collect metrics summaries
        metrics_summary = {}
        for metric_type in self.metrics_collector.get_all_metric_types():
            stats = self.metrics_collector.get_metric_statistics(metric_type, time_range)
            if stats.count > 0:
                metrics_summary[metric_type.value] = stats.to_dict()
        
        # Get alerts
        alerts = self.alert_manager.get_alerts(time_range=time_range)
        alert_data = [
            {
                'level': alert.level.value,
                'metric_type': alert.metric_type.value,
                'message': alert.message,
                'value': alert.value,
                'threshold': alert.threshold,
                'timestamp': alert.timestamp.isoformat()
            }
            for alert in alerts
        ]
        
        # Get system trends
        system_trends = self.system_monitor.get_system_trends(time_range)
        trend_data = {
            name: {
                'direction': trend.trend_direction,
                'sample_count': trend.sample_count,
                'time_span_minutes': trend.time_span_minutes
            }
            for name, trend in system_trends.items()
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(time_range)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'time_range_hours': time_range.total_seconds() / 3600,
            'metrics_summary': metrics_summary,
            'operation_statistics': self.operation_tracker.get_operation_statistics(),
            'alerts': alert_data,
            'system_trends': trend_data,
            'recommendations': recommendations,
            'system_health': self.get_system_health()
        }
    
    def get_profiling_report(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive profiling report"""
        return self.profiler.get_combined_report(profile_name)
    
    def configure_alerts(
        self,
        thresholds: Optional[Dict[MetricType, float]] = None,
        notification_channels: Optional[Dict[str, Callable]] = None
    ):
        """
        Configure alert settings
        
        Args:
            thresholds: Alert thresholds by metric type
            notification_channels: Notification channels
        """
        if thresholds:
            for metric_type, threshold in thresholds.items():
                self.alert_manager.set_alert_threshold(metric_type, threshold)
                self.threshold_manager.set_threshold(metric_type, threshold, "user_configured")
        
        if notification_channels:
            for name, handler in notification_channels.items():
                self.alert_notifier.register_channel(name, handler)
    
    def _setup_default_alert_handlers(self):
        """Setup default alert handlers"""
        # Register default notification channels
        self.alert_notifier.register_channel("log", log_alert_handler)
        self.alert_notifier.register_channel("console", console_alert_handler)
        
        # Setup notification rules
        self.alert_notifier.add_notification_rule(
            "log",
            [AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
        )
        
        self.alert_notifier.add_notification_rule(
            "console",
            [AlertLevel.CRITICAL]
        )
    
    def _handle_metric_alert(self, alert: PerformanceAlert):
        """Handle metric-based alerts"""
        logger.info(f"Handling alert: {alert.message}")
        
        # Check for system resource alerts
        if alert.metric_type in [MetricType.CPU_USAGE, MetricType.MEMORY_USAGE]:
            system_alerts = self.resource_alert_monitor.check_resource_alerts()
            for sys_alert in system_alerts:
                logger.warning(f"System alert: {sys_alert['message']}")
    
    def _generate_recommendations(self, time_range: timedelta) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Check operation performance
        op_stats = self.operation_tracker.get_operation_statistics()
        
        for op_name, stats in op_stats.items():
            if stats['avg_time'] > 5.0:  # Slow operations
                recommendations.append(
                    f"Operation '{op_name}' has high average execution time ({stats['avg_time']:.2f}s). "
                    f"Consider optimization."
                )
            
            if stats['error_rate'] > 5:  # High error rate
                recommendations.append(
                    f"Operation '{op_name}' has high error rate ({stats['error_rate']:.1f}%). "
                    f"Review error handling and input validation."
                )
        
        # Check system resources
        health = self.system_monitor.get_system_health()
        metrics = health.get('metrics', {})
        
        if metrics.get('memory_percent', 0) > 80:
            recommendations.append(
                f"High memory usage ({metrics['memory_percent']:.1f}%). "
                f"Consider implementing memory optimization or increasing available memory."
            )
        
        if metrics.get('cpu_percent', 0) > 80:
            recommendations.append(
                f"High CPU usage ({metrics['cpu_percent']:.1f}%). "
                f"Consider optimizing compute-intensive operations or scaling resources."
            )
        
        # Check alerts frequency
        recent_alerts = self.alert_manager.get_alerts(time_range=time_range)
        if len(recent_alerts) > 10:
            recommendations.append(
                f"High number of performance alerts ({len(recent_alerts)} in last {time_range.total_seconds()/3600:.1f} hours). "
                f"Review system performance and consider scaling."
            )
        
        return recommendations


# Global performance monitor instance
performance_monitor = PerformanceMonitorService()

# Convenience decorators
def track_performance(operation_name: Optional[str] = None, **context):
    """Decorator to track function performance"""
    return performance_monitor.track_function(operation_name, **context)
