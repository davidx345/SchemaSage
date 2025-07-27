"""
Analytics data collection and tracking
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import uuid

from .base import AnalyticsDataPoint, AnalyticsMetricType, SchemaUsagePattern, PerformanceMetric

logger = logging.getLogger(__name__)

class AnalyticsDataCollector:
    """Collects and stores analytics data"""
    
    def __init__(self):
        self.data_points: List[AnalyticsDataPoint] = []
        self.usage_patterns: Dict[str, SchemaUsagePattern] = {}
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.schema_operations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Background cleanup task
        asyncio.create_task(self._cleanup_old_data())
    
    async def track_schema_usage(
        self,
        schema_id: str,
        operation: str,
        user_id: str,
        table_name: Optional[str] = None,
        column_names: Optional[List[str]] = None,
        execution_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track schema usage event"""
        try:
            # Create data point
            data_point = AnalyticsDataPoint(
                id=str(uuid.uuid4()),
                metric_type=AnalyticsMetricType.USAGE_FREQUENCY,
                value=1.0,
                timestamp=datetime.now(),
                schema_id=schema_id,
                user_id=user_id,
                operation=operation,
                metadata=metadata or {}
            )
            
            self.data_points.append(data_point)
            
            # Update usage patterns
            await self._update_usage_patterns(
                schema_id, operation, user_id, table_name, column_names
            )
            
            # Track performance if provided
            if execution_time is not None:
                await self._track_performance(operation, execution_time, metadata or {})
            
            logger.debug(f"Tracked schema usage: {schema_id}, {operation}, {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking schema usage: {e}")
    
    async def _update_usage_patterns(
        self,
        schema_id: str,
        operation: str,
        user_id: str,
        table_name: Optional[str],
        column_names: Optional[List[str]]
    ):
        """Update usage patterns for schema"""
        if schema_id not in self.usage_patterns:
            self.usage_patterns[schema_id] = SchemaUsagePattern(
                schema_id=schema_id,
                total_operations=0,
                unique_users=0,
                peak_usage_time=datetime.now(),
                most_accessed_tables=[],
                operation_distribution={},
                user_activity_distribution={},
                temporal_patterns={},
                anomaly_scores={}
            )
        
        pattern = self.usage_patterns[schema_id]
        pattern.total_operations += 1
        
        # Update operation distribution
        if operation not in pattern.operation_distribution:
            pattern.operation_distribution[operation] = 0
        pattern.operation_distribution[operation] += 1
        
        # Update user activity
        if user_id not in pattern.user_activity_distribution:
            pattern.user_activity_distribution[user_id] = 0
        pattern.user_activity_distribution[user_id] += 1
        
        # Update unique users count
        pattern.unique_users = len(pattern.user_activity_distribution)
        
        # Track table access
        if table_name:
            self._update_table_access(pattern, table_name)
    
    def _update_table_access(self, pattern: SchemaUsagePattern, table_name: str):
        """Update table access statistics"""
        # Convert to dict for easier manipulation
        table_access = dict(pattern.most_accessed_tables)
        
        if table_name not in table_access:
            table_access[table_name] = 0
        table_access[table_name] += 1
        
        # Convert back to sorted list of tuples
        pattern.most_accessed_tables = sorted(
            table_access.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Keep top 10
    
    async def _track_performance(self, operation: str, execution_time: float, metadata: Dict[str, Any]):
        """Track performance metrics"""
        # Store execution time
        self.performance_metrics[operation].append(execution_time)
        
        # Create performance data point
        perf_data_point = AnalyticsDataPoint(
            id=str(uuid.uuid4()),
            metric_type=AnalyticsMetricType.PERFORMANCE,
            value=execution_time,
            timestamp=datetime.now(),
            operation=operation,
            metadata=metadata
        )
        
        self.data_points.append(perf_data_point)
    
    async def get_usage_pattern(self, schema_id: str) -> Optional[SchemaUsagePattern]:
        """Get usage pattern for schema"""
        return self.usage_patterns.get(schema_id)
    
    async def get_performance_metrics(self, operation: str) -> Optional[PerformanceMetric]:
        """Get performance metrics for operation"""
        if operation not in self.performance_metrics:
            return None
        
        times = self.performance_metrics[operation]
        if not times:
            return None
        
        times.sort()
        n = len(times)
        
        return PerformanceMetric(
            operation=operation,
            average_duration=sum(times) / n,
            p50_duration=times[n // 2],
            p95_duration=times[int(n * 0.95)] if n > 20 else times[-1],
            p99_duration=times[int(n * 0.99)] if n > 100 else times[-1],
            error_rate=0.0,  # TODO: Track errors
            throughput=n / (24 * 3600),  # Operations per second (rough estimate)
            sample_count=n,
            time_period=(datetime.now() - timedelta(days=1), datetime.now())
        )
    
    async def get_data_points(
        self,
        metric_type: Optional[AnalyticsMetricType] = None,
        schema_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[AnalyticsDataPoint]:
        """Get filtered data points"""
        filtered_points = self.data_points
        
        # Apply filters
        if metric_type:
            filtered_points = [p for p in filtered_points if p.metric_type == metric_type]
        
        if schema_id:
            filtered_points = [p for p in filtered_points if p.schema_id == schema_id]
        
        if user_id:
            filtered_points = [p for p in filtered_points if p.user_id == user_id]
        
        if start_time:
            filtered_points = [p for p in filtered_points if p.timestamp >= start_time]
        
        if end_time:
            filtered_points = [p for p in filtered_points if p.timestamp <= end_time]
        
        # Sort by timestamp
        filtered_points.sort(key=lambda p: p.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            filtered_points = filtered_points[:limit]
        
        return filtered_points
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get summary of analytics data"""
        total_data_points = len(self.data_points)
        unique_schemas = len(set(p.schema_id for p in self.data_points if p.schema_id))
        unique_users = len(set(p.user_id for p in self.data_points if p.user_id))
        
        # Operation distribution
        operation_dist = Counter(p.operation for p in self.data_points if p.operation)
        
        # Recent activity (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_points = [p for p in self.data_points if p.timestamp >= recent_cutoff]
        
        return {
            'total_data_points': total_data_points,
            'unique_schemas': unique_schemas,
            'unique_users': unique_users,
            'operation_distribution': dict(operation_dist.most_common(10)),
            'recent_activity_count': len(recent_points),
            'tracked_schemas': len(self.usage_patterns),
            'tracked_operations': len(self.performance_metrics)
        }
    
    async def _cleanup_old_data(self):
        """Background task to cleanup old data"""
        while True:
            try:
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
                # Remove data points older than 30 days
                cutoff_time = datetime.now() - timedelta(days=30)
                original_count = len(self.data_points)
                
                self.data_points = [
                    p for p in self.data_points 
                    if p.timestamp >= cutoff_time
                ]
                
                removed_count = original_count - len(self.data_points)
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} old analytics data points")
                
                # Cleanup old performance metrics
                for operation in list(self.performance_metrics.keys()):
                    if len(self.performance_metrics[operation]) > 10000:
                        # Keep only the most recent 10000 measurements
                        self.performance_metrics[operation] = self.performance_metrics[operation][-10000:]
                
            except Exception as e:
                logger.error(f"Error in analytics cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
