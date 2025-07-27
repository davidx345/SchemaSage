"""
Metrics collection and aggregation
"""
import threading
import time
import logging
from typing import Dict, List, Union
from collections import defaultdict
from datetime import datetime, timedelta

from .base import Metric, MetricType

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.metric_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self.retention_hours = 24
        self.aggregation_intervals = [60, 300, 3600]  # 1min, 5min, 1hour
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread for metric cleanup"""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_old_metrics()
                    time.sleep(3600)  # Cleanup every hour
                except Exception as e:
                    logger.error(f"Error in metrics cleanup: {e}")
                    time.sleep(60)
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType,
        tags: Dict[str, str] = None,
        unit: str = "",
        description: str = ""
    ):
        """Record a metric measurement"""
        
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            unit=unit,
            description=description
        )
        
        with self.metric_locks[name]:
            self.metrics[name].append(metric)
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        self.record_metric(name, value, MetricType.COUNTER, tags)
    
    def set_gauge(self, name: str, value: Union[int, float], tags: Dict[str, str] = None):
        """Set a gauge metric value"""
        self.record_metric(name, value, MetricType.GAUGE, tags)
    
    def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timer metric"""
        self.record_metric(name, duration_ms, MetricType.TIMER, tags, "ms")
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram metric"""
        self.record_metric(name, value, MetricType.HISTOGRAM, tags)
    
    def get_metrics(self, name: str, since: datetime = None) -> List[Metric]:
        """Get metrics for a specific name"""
        with self.metric_locks[name]:
            metrics = self.metrics[name]
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            
            return metrics.copy()
    
    def get_latest_metric(self, name: str) -> Metric:
        """Get the latest metric value"""
        with self.metric_locks[name]:
            metrics = self.metrics[name]
            return metrics[-1] if metrics else None
    
    def aggregate_metrics(
        self,
        name: str,
        interval_seconds: int,
        since: datetime = None
    ) -> List[Dict]:
        """Aggregate metrics over time intervals"""
        
        metrics = self.get_metrics(name, since)
        if not metrics:
            return []
        
        # Group metrics by time intervals
        buckets = defaultdict(list)
        
        for metric in metrics:
            # Round timestamp to interval boundary
            timestamp = metric.timestamp
            bucket_time = timestamp.replace(
                second=(timestamp.second // interval_seconds) * interval_seconds,
                microsecond=0
            )
            buckets[bucket_time].append(metric)
        
        # Aggregate each bucket
        aggregated = []
        for bucket_time, bucket_metrics in sorted(buckets.items()):
            if bucket_metrics[0].metric_type == MetricType.COUNTER:
                # Sum counters
                total_value = sum(m.value for m in bucket_metrics)
                aggregated.append({
                    'timestamp': bucket_time,
                    'value': total_value,
                    'count': len(bucket_metrics),
                    'type': 'sum'
                })
            
            elif bucket_metrics[0].metric_type in [MetricType.GAUGE, MetricType.TIMER, MetricType.HISTOGRAM]:
                # Calculate statistics for gauges/timers/histograms
                values = [m.value for m in bucket_metrics]
                aggregated.append({
                    'timestamp': bucket_time,
                    'value': sum(values) / len(values),  # Average
                    'min': min(values),
                    'max': max(values),
                    'count': len(values),
                    'type': 'stats'
                })
        
        return aggregated
    
    def _cleanup_old_metrics(self):
        """Remove old metrics beyond retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        for name in list(self.metrics.keys()):
            with self.metric_locks[name]:
                original_count = len(self.metrics[name])
                self.metrics[name] = [
                    m for m in self.metrics[name] 
                    if m.timestamp >= cutoff_time
                ]
                removed_count = original_count - len(self.metrics[name])
                
                if removed_count > 0:
                    logger.debug(f"Cleaned up {removed_count} old metrics for {name}")
    
    def get_metric_summary(self) -> Dict[str, Dict]:
        """Get summary of all collected metrics"""
        summary = {}
        
        for name in self.metrics:
            with self.metric_locks[name]:
                metrics = self.metrics[name]
                if metrics:
                    latest = metrics[-1]
                    summary[name] = {
                        'count': len(metrics),
                        'latest_value': latest.value,
                        'latest_timestamp': latest.timestamp.isoformat(),
                        'metric_type': latest.metric_type.value,
                        'unit': latest.unit,
                        'description': latest.description
                    }
        
        return summary
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format"""
        if format_type == "json":
            import json
            return json.dumps(self.get_metric_summary(), indent=2, default=str)
        
        elif format_type == "prometheus":
            # Export in Prometheus format
            lines = []
            for name, info in self.get_metric_summary().items():
                metric_type = info['metric_type']
                value = info['latest_value']
                
                # Prometheus metric format
                lines.append(f"# HELP {name} {info.get('description', '')}")
                lines.append(f"# TYPE {name} {metric_type}")
                lines.append(f"{name} {value}")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def clear_metrics(self, name: str = None):
        """Clear metrics (for testing or reset)"""
        if name:
            with self.metric_locks[name]:
                self.metrics[name].clear()
        else:
            for metric_name in list(self.metrics.keys()):
                with self.metric_locks[metric_name]:
                    self.metrics[metric_name].clear()


class MetricTimer:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, metric_name: str, tags: Dict[str, str] = None):
        self.collector = collector
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.collector.record_timer(self.metric_name, duration_ms, self.tags)


def timer(metric_name: str, collector: MetricsCollector, tags: Dict[str, str] = None):
    """Decorator for timing function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with MetricTimer(collector, metric_name, tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator
