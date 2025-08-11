"""
Monitoring & Alerting Service - Modularized
Phase 4: Real-time Monitoring, Alerts & Health Checks
"""

# Import all monitoring services from modular structure
from .monitoring.monitoring_engine import MonitoringEngine
from .monitoring.health_check_service import HealthCheckService
from .monitoring.notification_service import NotificationService
from .monitoring.dashboard_service import DashboardService

# Export classes for backward compatibility
__all__ = [
    'MonitoringEngine',
    'HealthCheckService', 
    'NotificationService',
    'DashboardService'
]
