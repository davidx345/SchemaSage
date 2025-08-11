"""
Performance Monitor Module
Continuous performance monitoring and analysis service.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.performance import PerformanceMetric, PerformanceReport, PerformanceBaseline, MetricType
from ...core.database import DatabaseManager
from ...utils.logging import get_logger

logger = get_logger(__name__)

class PerformanceMonitor:
    """Continuous performance monitoring service."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.baselines: Dict[str, PerformanceBaseline] = {}
    
    async def collect_performance_metrics(
        self,
        connection_id: str,
        workspace_id: str,
        session: AsyncSession
    ) -> List[PerformanceMetric]:
        """Collect current performance metrics."""
        
        connection = await self.db_manager.get_connection(connection_id)
        metrics = []
        
        try:
            # Database-specific metrics collection
            db_metrics = await self._collect_database_metrics(connection)
            
            for metric_name, value in db_metrics.items():
                metric = PerformanceMetric(
                    workspace_id=workspace_id,
                    connection_id=connection_id,
                    metric_name=metric_name,
                    metric_type=self._classify_metric_type(metric_name),
                    value=value,
                    unit=self._get_metric_unit(metric_name)
                )
                metrics.append(metric)
        
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
        
        return metrics
    
    async def _collect_database_metrics(self, connection: Any) -> Dict[str, float]:
        """Collect database-specific performance metrics."""
        
        metrics = {}
        
        try:
            # PostgreSQL example metrics
            metric_queries = {
                'active_connections': "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'",
                'cache_hit_ratio': """
                    SELECT round(
                        (sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read) + 1)) * 100, 2
                    ) FROM pg_statio_user_tables
                """,
                'average_query_time': """
                    SELECT avg(mean_exec_time) FROM pg_stat_statements 
                    WHERE calls > 10
                """,
                'database_size_mb': """
                    SELECT round(pg_database_size(current_database()) / (1024*1024)::numeric, 2)
                """
            }
            
            for metric_name, query in metric_queries.items():
                try:
                    async with connection.execute(text(query)) as result:
                        value = await result.fetchone()
                        if value and value[0] is not None:
                            metrics[metric_name] = float(value[0])
                except Exception as e:
                    logger.warning(f"Could not collect metric {metric_name}: {e}")
        
        except Exception as e:
            logger.warning(f"Database metrics collection failed: {e}")
        
        return metrics
    
    def _classify_metric_type(self, metric_name: str) -> MetricType:
        """Classify metric type based on name."""
        
        if 'time' in metric_name.lower() or 'latency' in metric_name.lower():
            return MetricType.PERFORMANCE
        elif 'connection' in metric_name.lower() or 'active' in metric_name.lower():
            return MetricType.AVAILABILITY
        elif 'size' in metric_name.lower() or 'memory' in metric_name.lower():
            return MetricType.CAPACITY
        else:
            return MetricType.PERFORMANCE
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get appropriate unit for metric."""
        
        if 'time' in metric_name.lower():
            return 'ms'
        elif 'ratio' in metric_name.lower() or 'percent' in metric_name.lower():
            return '%'
        elif 'size' in metric_name.lower() and 'mb' in metric_name.lower():
            return 'MB'
        elif 'connection' in metric_name.lower():
            return 'count'
        else:
            return 'unit'
    
    async def generate_performance_report(
        self,
        workspace_id: str,
        connection_id: str,
        session: AsyncSession,
        time_range_hours: int = 24
    ) -> PerformanceReport:
        """Generate comprehensive performance report."""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        report = PerformanceReport(
            workspace_id=workspace_id,
            connection_id=connection_id,
            report_period_start=start_time,
            report_period_end=end_time
        )
        
        try:
            # Collect current metrics
            current_metrics = await self.collect_performance_metrics(connection_id, workspace_id, session)
            
            # Calculate summary statistics
            report.summary_statistics = self._calculate_summary_stats(current_metrics)
            
            # Identify performance trends
            report.performance_trends = await self._analyze_performance_trends(
                workspace_id, connection_id, start_time, end_time, session
            )
            
            # Generate recommendations
            report.recommendations = await self._generate_performance_recommendations(
                current_metrics, report.performance_trends
            )
            
        except Exception as e:
            logger.error(f"Performance report generation failed: {e}")
            report.error_message = str(e)
        
        return report
    
    def _calculate_summary_stats(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Calculate summary statistics from metrics."""
        
        if not metrics:
            return {}
        
        df = pd.DataFrame([{
            'metric_name': m.metric_name,
            'value': m.value,
            'metric_type': m.metric_type
        } for m in metrics])
        
        return {
            'total_metrics': len(metrics),
            'performance_metrics': len(df[df['metric_type'] == MetricType.PERFORMANCE]),
            'capacity_metrics': len(df[df['metric_type'] == MetricType.CAPACITY]),
            'availability_metrics': len(df[df['metric_type'] == MetricType.AVAILABILITY]),
            'average_values': df.groupby('metric_name')['value'].mean().to_dict()
        }
    
    async def _analyze_performance_trends(
        self,
        workspace_id: str,
        connection_id: str,
        start_time: datetime,
        end_time: datetime,
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Analyze performance trends over time."""
        
        # In a real implementation, this would query historical metrics
        # For now, return mock trends
        return [
            {
                'metric': 'average_query_time',
                'trend': 'increasing',
                'change_percentage': 15.5,
                'significance': 'moderate'
            },
            {
                'metric': 'cache_hit_ratio',
                'trend': 'stable',
                'change_percentage': 2.1,
                'significance': 'low'
            }
        ]
    
    async def _generate_performance_recommendations(
        self,
        metrics: List[PerformanceMetric],
        trends: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate performance optimization recommendations."""
        
        recommendations = []
        
        # Analyze current metrics
        for metric in metrics:
            if metric.metric_name == 'cache_hit_ratio' and metric.value < 90:
                recommendations.append("Cache hit ratio is below 90% - consider increasing buffer pool size")
            
            if metric.metric_name == 'active_connections' and metric.value > 100:
                recommendations.append("High number of active connections - consider connection pooling")
        
        # Analyze trends
        for trend in trends:
            if trend['trend'] == 'increasing' and trend['change_percentage'] > 10:
                recommendations.append(f"Performance degradation detected in {trend['metric']} - investigate recent changes")
        
        return recommendations
