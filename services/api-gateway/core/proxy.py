"""
Core proxy functionality for API Gateway
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging
from typing import Dict, Any
from config.settings import get_service_config

logger = logging.getLogger(__name__)

class ProxyService:
    """Service for proxying requests to microservices"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def proxy_request(self, service_name: str, path: str, request: Request) -> JSONResponse:
        """Proxy request to specified microservice."""
        service_config = get_service_config(service_name)
        
        if not service_config:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
        
        service_url = service_config["url"]
        target_url = f"{service_url}{path}"
        
        try:
            # Get request body
            body = await request.body()
            
            # Prepare headers (exclude host and content-length)
            headers = {
                key: value for key, value in request.headers.items()
                if key.lower() not in ["host", "content-length"]
            }
            
            # Make request to target service
            async with self.client as client:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    params=request.query_params,
                    timeout=service_config.get("timeout", 30)
                )
                
                # Return response
                return JSONResponse(
                    content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"response": response.text},
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
        except httpx.TimeoutException:
            logger.error(f"Timeout when proxying to {service_name} at {target_url}")
            raise HTTPException(status_code=504, detail="Service timeout")
        except httpx.ConnectError:
            logger.error(f"Connection error when proxying to {service_name} at {target_url}")
            raise HTTPException(status_code=503, detail="Service unavailable")
        except Exception as e:
            logger.error(f"Error proxying request to {service_name}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal proxy error")
    
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        service_config = get_service_config(service_name)
        
        if not service_config:
            return {"status": "unknown", "message": "Service not configured"}
        
        health_url = f"{service_config['url']}{service_config['health_endpoint']}"
        
        try:
            async with self.client as client:
                response = await client.get(health_url, timeout=5.0)
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "response_time": response.elapsed.total_seconds(),
                        "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "status_code": response.status_code,
                        "message": response.text
                    }
                    
        except httpx.TimeoutException:
            return {"status": "timeout", "message": "Health check timed out"}
        except httpx.ConnectError:
            return {"status": "unreachable", "message": "Cannot connect to service"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Global proxy service instance
proxy_service = ProxyService()
