"""
Health monitoring for API Gateway
"""
from typing import Dict, Any, List
import logging
from core.proxy import proxy_service
from config.settings import SERVICES

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitor health of all microservices"""
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """Get health status of all services."""
        service_statuses = {}
        overall_healthy = True
        
        for service_name in SERVICES.keys():
            try:
                health_data = await proxy_service.check_service_health(service_name)
                service_statuses[service_name] = health_data
                
                if health_data["status"] not in ["healthy"]:
                    overall_healthy = False
                    
            except Exception as e:
                logger.error(f"Error checking health of {service_name}: {str(e)}")
                service_statuses[service_name] = {
                    "status": "error",
                    "message": str(e)
                }
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "services": service_statuses,
            "total_services": len(SERVICES),
            "healthy_services": len([s for s in service_statuses.values() if s["status"] == "healthy"])
        }
    
    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status of a specific service."""
        if service_name not in SERVICES:
            return {
                "status": "not_found",
                "message": f"Service {service_name} is not configured"
            }
        
        return await proxy_service.check_service_health(service_name)

# Global health monitor instance
health_monitor = HealthMonitor()
