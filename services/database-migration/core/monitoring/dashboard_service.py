"""
Dashboard Service - Monitoring dashboard data management
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.monitoring import MonitoringDashboard
from ...core.database import DatabaseManager
from ...utils.logging import get_logger
from ...utils.exceptions import MonitoringError

logger = get_logger(__name__)

class DashboardService:
    """Monitoring dashboard service."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def get_dashboard_data(
        self,
        dashboard_id: str,
        workspace_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        
        try:
            # Load dashboard configuration
            dashboard = await self._load_dashboard(dashboard_id, session)
            
            # Collect data for each widget
            widget_data = {}
            for widget in dashboard.widgets:
                data = await self._get_widget_data(widget, workspace_id, session)
                widget_data[widget.get("id")] = data
            
            return {
                "dashboard": dashboard,
                "data": widget_data,
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Dashboard data collection failed: {e}")
            raise MonitoringError(f"Dashboard data collection failed: {e}")
    
    async def _load_dashboard(
        self, 
        dashboard_id: str, 
        session: AsyncSession
    ) -> MonitoringDashboard:
        """Load dashboard configuration."""
        
        # Return sample dashboard
        return MonitoringDashboard(
            dashboard_id=dashboard_id,
            workspace_id="sample_workspace",
            name="System Performance Dashboard",
            description="Real-time system performance metrics",
            widgets=[
                {
                    "id": "query_performance",
                    "type": "line_chart",
                    "title": "Average Query Time",
                    "metric": "average_query_time",
                    "time_range": "1h"
                },
                {
                    "id": "cache_hit_ratio",
                    "type": "gauge",
                    "title": "Cache Hit Ratio",
                    "metric": "cache_hit_ratio",
                    "min_value": 0,
                    "max_value": 100
                },
                {
                    "id": "active_connections",
                    "type": "number",
                    "title": "Active Connections",
                    "metric": "active_connections"
                }
            ],
            owner_id="system"
        )
    
    async def _get_widget_data(
        self, 
        widget: Dict[str, Any], 
        workspace_id: str, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get data for a specific widget."""
        
        widget_type = widget.get("type")
        metric_name = widget.get("metric")
        
        if widget_type == "line_chart":
            return await self._get_time_series_data(metric_name, widget.get("time_range", "1h"))
        elif widget_type == "gauge":
            return await self._get_current_value(metric_name)
        elif widget_type == "number":
            return await self._get_current_value(metric_name)
        else:
            return {"error": f"Unknown widget type: {widget_type}"}
    
    async def _get_time_series_data(self, metric_name: str, time_range: str) -> Dict[str, Any]:
        """Get time series data for a metric."""
        
        # Generate sample time series data
        end_time = datetime.utcnow()
        
        if time_range == "1h":
            start_time = end_time - timedelta(hours=1)
            interval = timedelta(minutes=5)
        elif time_range == "24h":
            start_time = end_time - timedelta(hours=24)
            interval = timedelta(hours=1)
        else:
            start_time = end_time - timedelta(hours=1)
            interval = timedelta(minutes=5)
        
        timestamps = []
        values = []
        
        current_time = start_time
        base_value = 500.0 if metric_name == "average_query_time" else 90.0
        
        while current_time <= end_time:
            timestamps.append(current_time.isoformat())
            # Add some random variation
            value = base_value + random.uniform(-base_value * 0.1, base_value * 0.1)
            values.append(round(value, 2))
            current_time += interval
        
        return {
            "timestamps": timestamps,
            "values": values,
            "metric": metric_name
        }
    
    async def _get_current_value(self, metric_name: str) -> Dict[str, Any]:
        """Get current value for a metric."""
        
        # Return sample current values
        if metric_name == "average_query_time":
            value = 485.7
        elif metric_name == "cache_hit_ratio":
            value = 92.3
        elif metric_name == "active_connections":
            value = 47
        else:
            value = 0
        
        return {
            "value": value,
            "metric": metric_name,
            "timestamp": datetime.utcnow().isoformat()
        }
