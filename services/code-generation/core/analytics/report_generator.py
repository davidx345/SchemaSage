"""
Analytics report generation and insights
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from .base import (
    AnalyticsQuery, AnalyticsDataPoint, AnalyticsInsight, 
    AnalyticsMetricType, TimeGranularity
)
from .data_collector import AnalyticsDataCollector

logger = logging.getLogger(__name__)

class AnalyticsReportGenerator:
    """Generates analytics reports and insights"""
    
    def __init__(self, data_collector: AnalyticsDataCollector):
        self.data_collector = data_collector
    
    async def generate_analytics_report(self, query: AnalyticsQuery) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        try:
            # Get filtered data points
            data_points = await self._filter_data_points(query)
            
            # Generate summary statistics
            summary_stats = await self._generate_summary_stats(data_points, query)
            
            # Generate time series data
            time_series = await self._generate_time_series(data_points, query)
            
            # Generate insights
            insights = await self._generate_insights(data_points, query)
            
            # Generate trends
            trends = await self._analyze_trends(data_points, query)
            
            return {
                'query': {
                    'metric_types': [mt.value for mt in query.metric_types],
                    'time_range': {
                        'start': query.start_time.isoformat(),
                        'end': query.end_time.isoformat()
                    },
                    'granularity': query.granularity.value,
                    'aggregation': query.aggregation
                },
                'summary': summary_stats,
                'time_series': time_series,
                'insights': insights,
                'trends': trends,
                'generated_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error generating analytics report: {e}")
            raise
    
    async def _filter_data_points(self, query: AnalyticsQuery) -> List[AnalyticsDataPoint]:
        """Filter data points based on query parameters"""
        data_points = await self.data_collector.get_data_points(
            start_time=query.start_time,
            end_time=query.end_time
        )
        
        # Filter by metric types
        if query.metric_types:
            data_points = [
                p for p in data_points 
                if p.metric_type in query.metric_types
            ]
        
        # Filter by schema IDs
        if query.schema_ids:
            data_points = [
                p for p in data_points 
                if p.schema_id in query.schema_ids
            ]
        
        # Filter by user IDs
        if query.user_ids:
            data_points = [
                p for p in data_points 
                if p.user_id in query.user_ids
            ]
        
        # Filter by operations
        if query.operations:
            data_points = [
                p for p in data_points 
                if p.operation in query.operations
            ]
        
        # Apply additional filters
        for key, value in query.filters.items():
            if isinstance(value, list):
                data_points = [
                    p for p in data_points
                    if p.metadata.get(key) in value
                ]
            else:
                data_points = [
                    p for p in data_points
                    if p.metadata.get(key) == value
                ]
        
        # Apply limit
        if query.limit:
            data_points = data_points[:query.limit]
        
        return data_points
    
    async def _generate_summary_stats(self, data_points: List[AnalyticsDataPoint], query: AnalyticsQuery) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not data_points:
            return {}
        
        values = [p.value for p in data_points]
        
        stats = {
            'count': len(data_points),
            'sum': sum(values),
            'mean': statistics.mean(values) if values else 0,
            'median': statistics.median(values) if values else 0,
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values) if values else 0,
            'max': max(values) if values else 0
        }
        
        # Add percentiles
        if values:
            sorted_values = sorted(values)
            n = len(sorted_values)
            stats.update({
                'p25': sorted_values[int(n * 0.25)] if n > 4 else sorted_values[0],
                'p75': sorted_values[int(n * 0.75)] if n > 4 else sorted_values[-1],
                'p95': sorted_values[int(n * 0.95)] if n > 20 else sorted_values[-1],
                'p99': sorted_values[int(n * 0.99)] if n > 100 else sorted_values[-1]
            })
        
        # Group statistics
        if query.group_by:
            group_stats = {}
            for group_field in query.group_by:
                groups = defaultdict(list)
                
                for point in data_points:
                    if group_field == 'schema_id':
                        key = point.schema_id
                    elif group_field == 'user_id':
                        key = point.user_id
                    elif group_field == 'operation':
                        key = point.operation
                    else:
                        key = point.metadata.get(group_field, 'unknown')
                    
                    groups[key].append(point.value)
                
                group_stats[group_field] = {}
                for key, group_values in groups.items():
                    if group_values:
                        group_stats[group_field][str(key)] = {
                            'count': len(group_values),
                            'sum': sum(group_values),
                            'mean': statistics.mean(group_values)
                        }
            
            stats['groups'] = group_stats
        
        return stats
    
    async def _generate_time_series(self, data_points: List[AnalyticsDataPoint], query: AnalyticsQuery) -> List[Dict[str, Any]]:
        """Generate time series data"""
        if not data_points:
            return []
        
        # Group by time buckets
        time_buckets = defaultdict(list)
        
        for point in data_points:
            bucket_time = self._get_time_bucket(point.timestamp, query.granularity)
            time_buckets[bucket_time].append(point.value)
        
        # Generate time series
        time_series = []
        for bucket_time in sorted(time_buckets.keys()):
            values = time_buckets[bucket_time]
            
            if query.aggregation == 'sum':
                aggregated_value = sum(values)
            elif query.aggregation == 'count':
                aggregated_value = len(values)
            elif query.aggregation == 'min':
                aggregated_value = min(values)
            elif query.aggregation == 'max':
                aggregated_value = max(values)
            else:  # avg
                aggregated_value = statistics.mean(values) if values else 0
            
            time_series.append({
                'timestamp': bucket_time.isoformat(),
                'value': aggregated_value,
                'count': len(values)
            })
        
        return time_series
    
    def _get_time_bucket(self, timestamp: datetime, granularity: TimeGranularity) -> datetime:
        """Get time bucket for timestamp based on granularity"""
        if granularity == TimeGranularity.MINUTE:
            return timestamp.replace(second=0, microsecond=0)
        elif granularity == TimeGranularity.HOUR:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif granularity == TimeGranularity.DAY:
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TimeGranularity.WEEK:
            days_since_monday = timestamp.weekday()
            week_start = timestamp - timedelta(days=days_since_monday)
            return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TimeGranularity.MONTH:
            return timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TimeGranularity.QUARTER:
            quarter_month = ((timestamp.month - 1) // 3) * 3 + 1
            return timestamp.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TimeGranularity.YEAR:
            return timestamp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return timestamp
    
    async def _generate_insights(self, data_points: List[AnalyticsDataPoint], query: AnalyticsQuery) -> List[Dict[str, Any]]:
        """Generate insights from data"""
        insights = []
        
        if not data_points:
            return insights
        
        # Usage pattern insights
        if AnalyticsMetricType.USAGE_FREQUENCY in query.metric_types:
            usage_insights = await self._analyze_usage_patterns(data_points)
            insights.extend(usage_insights)
        
        # Performance insights
        if AnalyticsMetricType.PERFORMANCE in query.metric_types:
            perf_insights = await self._analyze_performance_patterns(data_points)
            insights.extend(perf_insights)
        
        # Anomaly detection
        anomaly_insights = await self._detect_anomalies(data_points)
        insights.extend(anomaly_insights)
        
        return insights
    
    async def _analyze_usage_patterns(self, data_points: List[AnalyticsDataPoint]) -> List[Dict[str, Any]]:
        """Analyze usage patterns"""
        insights = []
        
        # Peak usage times
        hour_counts = defaultdict(int)
        for point in data_points:
            hour_counts[point.timestamp.hour] += 1
        
        if hour_counts:
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])
            insights.append({
                'type': 'peak_usage',
                'title': 'Peak Usage Time',
                'description': f'Highest activity occurs at {peak_hour[0]}:00 with {peak_hour[1]} operations',
                'confidence': 0.8,
                'category': 'usage_pattern'
            })
        
        return insights
    
    async def _analyze_performance_patterns(self, data_points: List[AnalyticsDataPoint]) -> List[Dict[str, Any]]:
        """Analyze performance patterns"""
        insights = []
        
        perf_points = [p for p in data_points if p.metric_type == AnalyticsMetricType.PERFORMANCE]
        if not perf_points:
            return insights
        
        values = [p.value for p in perf_points]
        if len(values) > 10:
            mean_value = statistics.mean(values)
            std_dev = statistics.stdev(values)
            
            # Check for slow operations
            slow_threshold = mean_value + 2 * std_dev
            slow_operations = [p for p in perf_points if p.value > slow_threshold]
            
            if slow_operations:
                insights.append({
                    'type': 'slow_operations',
                    'title': 'Slow Operations Detected',
                    'description': f'Found {len(slow_operations)} operations exceeding normal response time',
                    'confidence': 0.9,
                    'category': 'performance'
                })
        
        return insights
    
    async def _detect_anomalies(self, data_points: List[AnalyticsDataPoint]) -> List[Dict[str, Any]]:
        """Detect anomalies in data"""
        insights = []
        
        # Simple anomaly detection based on statistical outliers
        values = [p.value for p in data_points]
        if len(values) > 20:
            q1 = statistics.quantiles(values, n=4)[0]
            q3 = statistics.quantiles(values, n=4)[2]
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [p for p in data_points if p.value < lower_bound or p.value > upper_bound]
            
            if outliers:
                insights.append({
                    'type': 'anomalies',
                    'title': 'Anomalous Data Points',
                    'description': f'Detected {len(outliers)} anomalous data points',
                    'confidence': 0.7,
                    'category': 'anomaly'
                })
        
        return insights
    
    async def _analyze_trends(self, data_points: List[AnalyticsDataPoint], query: AnalyticsQuery) -> Dict[str, Any]:
        """Analyze trends in data"""
        if not data_points:
            return {}
        
        # Sort by timestamp
        sorted_points = sorted(data_points, key=lambda p: p.timestamp)
        
        # Calculate trend
        if len(sorted_points) > 5:
            values = [p.value for p in sorted_points]
            x_values = list(range(len(values)))
            
            # Simple linear regression for trend
            n = len(values)
            sum_x = sum(x_values)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(x_values, values))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            trend_direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
            trend_strength = abs(slope)
            
            return {
                'direction': trend_direction,
                'strength': trend_strength,
                'slope': slope,
                'data_points': len(sorted_points)
            }
        
        return {'direction': 'unknown', 'strength': 0, 'data_points': len(sorted_points)}
