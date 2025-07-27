"""
Performance alerting system
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque

from .models import (
    MetricType, AlertLevel, PerformanceAlert, PerformanceMetric,
    DEFAULT_ALERT_THRESHOLDS, create_alert, is_metric_above_threshold
)

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages performance alerts and notifications
    """
    
    def __init__(self, alert_thresholds: Optional[Dict[MetricType, float]] = None):
        self.alert_thresholds = alert_thresholds or DEFAULT_ALERT_THRESHOLDS.copy()
        self.alerts: List[PerformanceAlert] = []
        self.alert_handlers: Dict[AlertLevel, List[Callable]] = defaultdict(list)
        
        # Alert state tracking
        self.recent_alerts: Dict[str, datetime] = {}
        self.alert_cooldown = timedelta(minutes=5)
        self.max_alerts = 1000
        
        # Alert statistics
        self.alert_stats: Dict[AlertLevel, int] = defaultdict(int)
        self.suppressed_alerts = 0
    
    def check_metric_alert(self, metric: PerformanceMetric) -> Optional[PerformanceAlert]:
        """
        Check if metric triggers an alert
        
        Args:
            metric: Performance metric to check
            
        Returns:
            Alert if threshold exceeded, None otherwise
        """
        if not is_metric_above_threshold(metric, self.alert_thresholds):
            return None
        
        threshold = self.alert_thresholds[metric.metric_type]
        alert_key = f"{metric.metric_type.value}_{threshold}"
        
        # Check cooldown
        if self._is_alert_suppressed(alert_key):
            self.suppressed_alerts += 1
            return None
        
        # Create alert
        alert = create_alert(
            metric.metric_type,
            metric.value,
            threshold,
            metric.context
        )
        
        # Record alert
        self.add_alert(alert)
        self.recent_alerts[alert_key] = alert.timestamp
        
        return alert
    
    def add_alert(self, alert: PerformanceAlert):
        """
        Add alert to the system
        
        Args:
            alert: Alert to add
        """
        self.alerts.append(alert)
        self.alert_stats[alert.level] += 1
        
        # Limit alert storage
        if len(self.alerts) > self.max_alerts:
            # Remove oldest alerts
            removed_alert = self.alerts.pop(0)
            self.alert_stats[removed_alert.level] -= 1
        
        # Trigger alert handlers
        self._trigger_alert_handlers(alert)
        
        logger.warning(f"Performance alert: {alert.message}")
    
    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        metric_type: Optional[MetricType] = None,
        time_range: Optional[timedelta] = None
    ) -> List[PerformanceAlert]:
        """
        Get alerts with optional filtering
        
        Args:
            level: Filter by alert level
            metric_type: Filter by metric type
            time_range: Filter by time range
            
        Returns:
            List of matching alerts
        """
        alerts = self.alerts.copy()
        
        # Apply filters
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if metric_type:
            alerts = [a for a in alerts if a.metric_type == metric_type]
        
        if time_range:
            cutoff = datetime.now() - time_range
            alerts = [a for a in alerts if a.timestamp >= cutoff]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_summary(self, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get summary of alerts
        
        Args:
            time_range: Optional time range filter
            
        Returns:
            Alert summary statistics
        """
        alerts = self.get_alerts(time_range=time_range)
        
        level_counts = defaultdict(int)
        metric_counts = defaultdict(int)
        
        for alert in alerts:
            level_counts[alert.level.value] += 1
            metric_counts[alert.metric_type.value] += 1
        
        return {
            'total_alerts': len(alerts),
            'by_level': dict(level_counts),
            'by_metric_type': dict(metric_counts),
            'suppressed_alerts': self.suppressed_alerts,
            'time_range_hours': time_range.total_seconds() / 3600 if time_range else None
        }
    
    def register_alert_handler(self, level: AlertLevel, handler: Callable[[PerformanceAlert], None]):
        """
        Register alert handler for specific level
        
        Args:
            level: Alert level to handle
            handler: Callback function for alert
        """
        self.alert_handlers[level].append(handler)
        logger.info(f"Registered alert handler for {level.value} alerts")
    
    def set_alert_threshold(self, metric_type: MetricType, threshold: float):
        """
        Set alert threshold for metric type
        
        Args:
            metric_type: Type of metric
            threshold: Threshold value
        """
        self.alert_thresholds[metric_type] = threshold
        logger.info(f"Set alert threshold for {metric_type.value}: {threshold}")
    
    def clear_alerts(self, older_than: Optional[timedelta] = None):
        """
        Clear alerts
        
        Args:
            older_than: Only clear alerts older than this duration
        """
        if older_than:
            cutoff = datetime.now() - older_than
            initial_count = len(self.alerts)
            self.alerts = [a for a in self.alerts if a.timestamp >= cutoff]
            cleared_count = initial_count - len(self.alerts)
            
            logger.info(f"Cleared {cleared_count} alerts older than {older_than}")
        else:
            self.alerts.clear()
            self.alert_stats.clear()
            self.suppressed_alerts = 0
            logger.info("Cleared all alerts")
    
    def _is_alert_suppressed(self, alert_key: str) -> bool:
        """Check if alert should be suppressed due to cooldown"""
        last_alert = self.recent_alerts.get(alert_key)
        if last_alert is None:
            return False
        
        return (datetime.now() - last_alert) < self.alert_cooldown
    
    def _trigger_alert_handlers(self, alert: PerformanceAlert):
        """Trigger registered alert handlers"""
        handlers = self.alert_handlers.get(alert.level, [])
        
        for handler in handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")


class ThresholdManager:
    """
    Manages dynamic alert thresholds
    """
    
    def __init__(self):
        self.thresholds: Dict[MetricType, float] = DEFAULT_ALERT_THRESHOLDS.copy()
        self.adaptive_thresholds: Dict[MetricType, Dict[str, Any]] = {}
        self.threshold_history: Dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=100))
    
    def set_threshold(self, metric_type: MetricType, threshold: float, reason: str = "manual"):
        """
        Set alert threshold for metric type
        
        Args:
            metric_type: Type of metric
            threshold: Threshold value
            reason: Reason for threshold change
        """
        old_threshold = self.thresholds.get(metric_type)
        self.thresholds[metric_type] = threshold
        
        # Record threshold change
        self.threshold_history[metric_type].append({
            'timestamp': datetime.now(),
            'old_threshold': old_threshold,
            'new_threshold': threshold,
            'reason': reason
        })
        
        logger.info(f"Updated {metric_type.value} threshold: {old_threshold} -> {threshold} ({reason})")
    
    def enable_adaptive_threshold(
        self,
        metric_type: MetricType,
        baseline_multiplier: float = 2.0,
        min_samples: int = 50
    ):
        """
        Enable adaptive threshold based on historical data
        
        Args:
            metric_type: Type of metric
            baseline_multiplier: Multiplier for baseline calculation
            min_samples: Minimum samples needed for adaptation
        """
        self.adaptive_thresholds[metric_type] = {
            'enabled': True,
            'baseline_multiplier': baseline_multiplier,
            'min_samples': min_samples,
            'last_update': datetime.now()
        }
        
        logger.info(f"Enabled adaptive threshold for {metric_type.value}")
    
    def update_adaptive_thresholds(self, recent_metrics: Dict[MetricType, List[float]]):
        """
        Update adaptive thresholds based on recent metrics
        
        Args:
            recent_metrics: Recent metric values by type
        """
        for metric_type, config in self.adaptive_thresholds.items():
            if not config['enabled']:
                continue
            
            values = recent_metrics.get(metric_type, [])
            if len(values) < config['min_samples']:
                continue
            
            # Calculate adaptive threshold
            baseline = sum(values) / len(values)  # Average
            new_threshold = baseline * config['baseline_multiplier']
            
            # Only update if significantly different
            current_threshold = self.thresholds.get(metric_type, 0)
            if abs(new_threshold - current_threshold) / current_threshold > 0.1:  # 10% change
                self.set_threshold(metric_type, new_threshold, "adaptive")
                config['last_update'] = datetime.now()
    
    def get_threshold(self, metric_type: MetricType) -> Optional[float]:
        """Get current threshold for metric type"""
        return self.thresholds.get(metric_type)
    
    def get_threshold_history(self, metric_type: MetricType) -> List[Dict[str, Any]]:
        """Get threshold change history"""
        return list(self.threshold_history.get(metric_type, []))


class AlertNotifier:
    """
    Handles alert notifications through various channels
    """
    
    def __init__(self):
        self.notification_channels = {}
        self.notification_rules = []
    
    def register_channel(self, name: str, handler: Callable[[PerformanceAlert], None]):
        """
        Register notification channel
        
        Args:
            name: Channel name
            handler: Notification handler function
        """
        self.notification_channels[name] = handler
        logger.info(f"Registered notification channel: {name}")
    
    def add_notification_rule(
        self,
        channel: str,
        levels: List[AlertLevel],
        metric_types: Optional[List[MetricType]] = None
    ):
        """
        Add notification rule
        
        Args:
            channel: Channel name
            levels: Alert levels to notify
            metric_types: Optional metric types filter
        """
        rule = {
            'channel': channel,
            'levels': levels,
            'metric_types': metric_types or []
        }
        self.notification_rules.append(rule)
        logger.info(f"Added notification rule for {channel}: {[l.value for l in levels]}")
    
    def notify(self, alert: PerformanceAlert):
        """
        Send notifications for alert
        
        Args:
            alert: Alert to notify about
        """
        for rule in self.notification_rules:
            # Check if alert matches rule
            if alert.level not in rule['levels']:
                continue
            
            if rule['metric_types'] and alert.metric_type not in rule['metric_types']:
                continue
            
            # Send notification
            channel_handler = self.notification_channels.get(rule['channel'])
            if channel_handler:
                try:
                    channel_handler(alert)
                    logger.info(f"Sent alert notification via {rule['channel']}")
                except Exception as e:
                    logger.error(f"Error sending notification via {rule['channel']}: {e}")


class AlertAggregator:
    """
    Aggregates and deduplicates alerts
    """
    
    def __init__(self, aggregation_window: timedelta = timedelta(minutes=1)):
        self.aggregation_window = aggregation_window
        self.pending_alerts: Dict[str, List[PerformanceAlert]] = defaultdict(list)
        self.last_flush = datetime.now()
    
    def add_alert(self, alert: PerformanceAlert) -> Optional[PerformanceAlert]:
        """
        Add alert to aggregator
        
        Args:
            alert: Alert to add
            
        Returns:
            Aggregated alert if window completed, None otherwise
        """
        # Group by metric type and level
        key = f"{alert.metric_type.value}_{alert.level.value}"
        self.pending_alerts[key].append(alert)
        
        # Check if aggregation window has passed
        if datetime.now() - self.last_flush >= self.aggregation_window:
            return self._flush_aggregated_alerts()
        
        return None
    
    def _flush_aggregated_alerts(self) -> Optional[PerformanceAlert]:
        """Flush and aggregate pending alerts"""
        if not self.pending_alerts:
            return None
        
        # Find most critical alert
        all_alerts = []
        for alerts_list in self.pending_alerts.values():
            all_alerts.extend(alerts_list)
        
        if not all_alerts:
            return None
        
        # Sort by severity (critical > error > warning > info)
        severity_order = {
            AlertLevel.CRITICAL: 4,
            AlertLevel.ERROR: 3,
            AlertLevel.WARNING: 2,
            AlertLevel.INFO: 1
        }
        
        all_alerts.sort(key=lambda a: severity_order.get(a.level, 0), reverse=True)
        most_critical = all_alerts[0]
        
        # Create aggregated alert
        if len(all_alerts) > 1:
            most_critical.message += f" (and {len(all_alerts) - 1} other alerts)"
        
        # Clear pending alerts
        self.pending_alerts.clear()
        self.last_flush = datetime.now()
        
        return most_critical


# Default alert handlers
def log_alert_handler(alert: PerformanceAlert):
    """Default log-based alert handler"""
    level_map = {
        AlertLevel.INFO: logger.info,
        AlertLevel.WARNING: logger.warning,
        AlertLevel.ERROR: logger.error,
        AlertLevel.CRITICAL: logger.critical
    }
    
    log_func = level_map.get(alert.level, logger.info)
    log_func(f"ALERT [{alert.level.value}]: {alert.message}")


def console_alert_handler(alert: PerformanceAlert):
    """Console alert handler"""
    timestamp = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] ALERT [{alert.level.value}]: {alert.message}")


def file_alert_handler(alert: PerformanceAlert):
    """File-based alert handler"""
    try:
        import os
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "performance_alerts.log")
        timestamp = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {alert.level.value}: {alert.message}\n")
    except Exception as e:
        logger.error(f"Error writing alert to file: {e}")
