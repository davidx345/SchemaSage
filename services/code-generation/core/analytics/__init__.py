"""
Analytics module initialization
"""
from .base import (
    AnalyticsMetricType,
    TimeGranularity,
    AnalyticsDataPoint,
    AnalyticsQuery,
    AnalyticsInsight,
    SchemaUsagePattern,
    PerformanceMetric
)
from .data_collector import AnalyticsDataCollector
from .report_generator import AnalyticsReportGenerator

# Main analytics engine class
class AdvancedAnalyticsEngine:
    """Advanced analytics engine for schema insights"""
    
    def __init__(self):
        self.data_collector = AnalyticsDataCollector()
        self.report_generator = AnalyticsReportGenerator(self.data_collector)
    
    async def track_schema_usage(
        self,
        schema_id: str,
        operation: str,
        user_id: str,
        table_name: str = None,
        column_names: List[str] = None,
        execution_time: float = None,
        metadata: Dict[str, Any] = None
    ):
        """Track schema usage event"""
        return await self.data_collector.track_schema_usage(
            schema_id, operation, user_id, table_name, column_names, execution_time, metadata
        )
    
    async def generate_analytics_report(self, query: AnalyticsQuery) -> Dict[str, Any]:
        """Generate analytics report"""
        return await self.report_generator.generate_analytics_report(query)
    
    async def get_usage_pattern(self, schema_id: str) -> SchemaUsagePattern:
        """Get usage pattern for schema"""
        return await self.data_collector.get_usage_pattern(schema_id)
    
    async def get_performance_metrics(self, operation: str) -> PerformanceMetric:
        """Get performance metrics for operation"""
        return await self.data_collector.get_performance_metrics(operation)

__all__ = [
    'AnalyticsMetricType',
    'TimeGranularity', 
    'AnalyticsDataPoint',
    'AnalyticsQuery',
    'AnalyticsInsight',
    'SchemaUsagePattern',
    'PerformanceMetric',
    'AnalyticsDataCollector',
    'AnalyticsReportGenerator',
    'AdvancedAnalyticsEngine'
]
