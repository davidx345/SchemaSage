"""
Core metrics collection and tracking functionality
"""

import time
import functools
import logging
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import threading
import asyncio
import psutil

from .models import (
    MetricType, PerformanceMetric, ActiveOperation, OperationStats,
    MetricStatistics, create_metric
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Core metrics collection and storage system
    """
    
    def __init__(self, max_metrics_per_type: int = 10000, retention_hours: int = 24):
        # Metrics storage
        self.metrics: Dict[MetricType, deque] = defaultdict(
            lambda: deque(maxlen=max_metrics_per_type)
        )
        
        # Operation tracking
        self.active_operations: Dict[str, ActiveOperation] = {}
        self.operation_stats: Dict[str, OperationStats] = {}
        
        # Configuration
        self.retention_hours = retention_hours
        self._lock = threading.Lock()
        
        # Cleanup tracking
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(minutes=30)
    
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
        metric = create_metric(metric_type, value, context, tags)
        
        with self._lock:
            self.metrics[metric_type].append(metric)
        
        # Periodic cleanup
        self._maybe_cleanup()
        
        logger.debug(f"Recorded {metric_type.value}: {value}")
        return metric
    
    def get_metrics(
        self,
        metric_type: MetricType,
        time_range: Optional[timedelta] = None,
        tags: Optional[List[str]] = None
    ) -> List[PerformanceMetric]:
        """
        Get metrics with optional filtering
        
        Args:
            metric_type: Type of metrics to retrieve
            time_range: Optional time range filter
            tags: Optional tags filter
            
        Returns:
            List of matching metrics
        """
        with self._lock:
            metrics = list(self.metrics[metric_type])
        
        # Apply time range filter
        if time_range:
            cutoff = datetime.now() - time_range
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        # Apply tags filter
        if tags:
            metrics = [
                m for m in metrics 
                if any(tag in m.tags for tag in tags)
            ]
        
        return sorted(metrics, key=lambda x: x.timestamp)
    
    def get_metric_statistics(
        self,
        metric_type: MetricType,
        time_range: Optional[timedelta] = None
    ) -> MetricStatistics:
        """
        Get statistical summary of metrics
        
        Args:
            metric_type: Type of metrics to analyze
            time_range: Optional time range filter
            
        Returns:
            Statistical summary
        """
        metrics = self.get_metrics(metric_type, time_range)
        values = [m.value for m in metrics]
        
        return MetricStatistics.from_values(values)
    
    def get_all_metric_types(self) -> List[MetricType]:
        """Get all metric types that have recorded data"""
        with self._lock:
            return list(self.metrics.keys())
    
    def clear_metrics(self, metric_type: Optional[MetricType] = None):
        """
        Clear metrics data
        
        Args:
            metric_type: Specific type to clear, or None to clear all
        """
        with self._lock:
            if metric_type:
                self.metrics[metric_type].clear()
            else:
                self.metrics.clear()
        
        logger.info(f"Cleared metrics: {metric_type.value if metric_type else 'all'}")
    
    def _maybe_cleanup(self):
        """Perform cleanup if interval has passed"""
        now = datetime.now()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_old_metrics()
            self._last_cleanup = now
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics based on retention policy"""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        
        with self._lock:
            for metric_type in self.metrics:
                # Remove old metrics from the beginning of deque
                while (self.metrics[metric_type] and 
                       self.metrics[metric_type][0].timestamp < cutoff):
                    self.metrics[metric_type].popleft()
        
        logger.debug("Cleaned up old metrics")


class OperationTracker:
    """
    Tracks operation performance and statistics
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.active_operations: Dict[str, ActiveOperation] = {}
        self.operation_stats: Dict[str, OperationStats] = {}
        self._lock = threading.Lock()
    
    @contextmanager
    def track_operation(self, operation_name: str, **context):
        """
        Context manager to track operation performance
        
        Args:
            operation_name: Name of the operation
            **context: Additional context data
            
        Yields:
            Operation ID for the tracked operation
        """
        operation_id = f"{operation_name}_{time.time()}_{id(threading.current_thread())}"
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create active operation
        active_op = ActiveOperation(
            operation_id=operation_id,
            name=operation_name,
            start_time=start_time,
            start_memory=start_memory,
            context=context
        )
        
        with self._lock:
            self.active_operations[operation_id] = active_op
        
        try:
            yield operation_id
            
            # Record successful completion
            end_time = time.time()
            execution_time = end_time - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_delta = end_memory - start_memory
            
            # Record metrics
            self.metrics_collector.record_metric(
                MetricType.EXECUTION_TIME,
                execution_time,
                context={'operation': operation_name, **context}
            )
            
            if abs(memory_delta) > 1:  # Only record significant memory changes
                self.metrics_collector.record_metric(
                    MetricType.MEMORY_USAGE,
                    memory_delta,
                    context={'operation': operation_name, **context}
                )
            
            # Update operation statistics
            self._update_operation_stats(operation_name, execution_time, is_error=False)
            
        except Exception as e:
            # Record error
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.metrics_collector.record_metric(
                MetricType.ERROR_RATE,
                1,
                context={'operation': operation_name, 'error': str(e), **context}
            )
            
            # Update operation statistics
            self._update_operation_stats(operation_name, execution_time, is_error=True)
            
            raise
        
        finally:
            with self._lock:
                self.active_operations.pop(operation_id, None)
    
    def track_function(self, operation_name: Optional[str] = None, **tracking_context):
        """
        Decorator to track function performance
        
        Args:
            operation_name: Custom operation name, defaults to function name
            **tracking_context: Additional context data
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.track_operation(op_name, **tracking_context):
                    return func(*args, **kwargs)
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.track_operation(op_name, **tracking_context):
                    return await func(*args, **kwargs)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    def get_active_operations(self) -> Dict[str, Dict[str, Any]]:
        """
        Get currently active operations
        
        Returns:
            Dictionary of active operations with their details
        """
        current_time = time.time()
        with self._lock:
            active = {}
            for op_id, op_data in self.active_operations.items():
                active[op_id] = {
                    'name': op_data.name,
                    'start_time': op_data.start_time,
                    'start_memory': op_data.start_memory,
                    'duration': current_time - op_data.start_time,
                    'context': op_data.context
                }
            return active
    
    def get_operation_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all tracked operations
        
        Returns:
            Dictionary of operation statistics
        """
        with self._lock:
            return {
                name: stats.to_dict() 
                for name, stats in self.operation_stats.items()
            }
    
    def get_operation_stats(self, operation_name: str) -> Optional[OperationStats]:
        """
        Get statistics for a specific operation
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Operation statistics or None if not found
        """
        with self._lock:
            return self.operation_stats.get(operation_name)
    
    def clear_operation_stats(self, operation_name: Optional[str] = None):
        """
        Clear operation statistics
        
        Args:
            operation_name: Specific operation to clear, or None to clear all
        """
        with self._lock:
            if operation_name:
                self.operation_stats.pop(operation_name, None)
            else:
                self.operation_stats.clear()
        
        logger.info(f"Cleared operation stats: {operation_name or 'all'}")
    
    def _update_operation_stats(self, operation_name: str, execution_time: float, is_error: bool):
        """Update operation statistics"""
        with self._lock:
            if operation_name not in self.operation_stats:
                self.operation_stats[operation_name] = OperationStats(name=operation_name)
            
            self.operation_stats[operation_name].update(execution_time, is_error)


class BatchMetricsCollector:
    """
    Collects metrics in batches for better performance
    """
    
    def __init__(self, metrics_collector: MetricsCollector, batch_size: int = 100, flush_interval: float = 5.0):
        self.metrics_collector = metrics_collector
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self._batch: List[PerformanceMetric] = []
        self._lock = threading.Lock()
        self._last_flush = time.time()
        self._flush_timer: Optional[threading.Timer] = None
    
    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Record a metric in batch mode
        
        Args:
            metric_type: Type of metric
            value: Metric value
            context: Additional context data
            tags: Metric tags
        """
        metric = create_metric(metric_type, value, context, tags)
        
        with self._lock:
            self._batch.append(metric)
            
            # Check if batch is full
            if len(self._batch) >= self.batch_size:
                self._flush_batch()
            else:
                # Set up timer for next flush if not already set
                if self._flush_timer is None:
                    self._flush_timer = threading.Timer(self.flush_interval, self._flush_batch)
                    self._flush_timer.start()
    
    def flush(self):
        """Force flush of current batch"""
        with self._lock:
            self._flush_batch()
    
    def _flush_batch(self):
        """Flush current batch to metrics collector"""
        if not self._batch:
            return
        
        # Cancel existing timer
        if self._flush_timer:
            self._flush_timer.cancel()
            self._flush_timer = None
        
        # Process batch
        batch_to_process = self._batch.copy()
        self._batch.clear()
        self._last_flush = time.time()
        
        # Release lock before processing
        with self._lock:
            pass
        
        # Record metrics
        for metric in batch_to_process:
            with self.metrics_collector._lock:
                self.metrics_collector.metrics[metric.metric_type].append(metric)
        
        logger.debug(f"Flushed batch of {len(batch_to_process)} metrics")
    
    def __del__(self):
        """Cleanup on destruction"""
        if self._flush_timer:
            self._flush_timer.cancel()
        self.flush()


class MemoryEfficientCollector:
    """
    Memory-efficient metrics collector using sampling
    """
    
    def __init__(self, sample_rate: float = 0.1, max_samples: int = 1000):
        self.sample_rate = sample_rate
        self.max_samples = max_samples
        self.metrics: Dict[MetricType, List[PerformanceMetric]] = defaultdict(list)
        self._lock = threading.Lock()
        self._sample_counter = 0
    
    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Record metric with sampling
        
        Args:
            metric_type: Type of metric
            value: Metric value
            context: Additional context data
            tags: Metric tags
        """
        import random
        
        # Sample based on rate
        if random.random() > self.sample_rate:
            return
        
        metric = create_metric(metric_type, value, context, tags)
        
        with self._lock:
            metrics_list = self.metrics[metric_type]
            
            # Add metric
            metrics_list.append(metric)
            
            # Keep only recent samples if over limit
            if len(metrics_list) > self.max_samples:
                # Remove oldest samples
                metrics_list[:] = metrics_list[-self.max_samples:]
    
    def get_sampled_metrics(self, metric_type: MetricType) -> List[PerformanceMetric]:
        """Get sampled metrics for a type"""
        with self._lock:
            return list(self.metrics[metric_type])
    
    def get_estimated_statistics(self, metric_type: MetricType) -> MetricStatistics:
        """Get estimated statistics from sampled data"""
        sampled_metrics = self.get_sampled_metrics(metric_type)
        values = [m.value for m in sampled_metrics]
        
        # Scale up count based on sample rate
        stats = MetricStatistics.from_values(values)
        if self.sample_rate > 0:
            stats.count = int(stats.count / self.sample_rate)
        
        return stats
