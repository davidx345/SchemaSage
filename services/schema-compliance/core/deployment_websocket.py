"""
Deployment WebSocket Manager
Handles real-time progress updates for cloud deployments via WebSocket
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DeploymentWebSocketManager:
    """Manages WebSocket connections for deployment progress updates"""
    
    def __init__(self):
        """Initialize WebSocket manager"""
        # Store active connections: {deployment_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, deployment_id: str, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection
        
        Args:
            deployment_id: The deployment to monitor
            websocket: The WebSocket connection
        """
        await websocket.accept()
        
        if deployment_id not in self.active_connections:
            self.active_connections[deployment_id] = []
        
        self.active_connections[deployment_id].append(websocket)
        logger.info(f"WebSocket connected for deployment {deployment_id}. Total connections: {len(self.active_connections[deployment_id])}")
        
        # Send connection success message
        await self.send_to_connection(websocket, {
            "type": "auth_success",
            "message": "Connected to deployment stream",
            "deployment_id": deployment_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, deployment_id: str, websocket: WebSocket):
        """
        Remove a WebSocket connection
        
        Args:
            deployment_id: The deployment being monitored
            websocket: The WebSocket connection to remove
        """
        if deployment_id in self.active_connections:
            if websocket in self.active_connections[deployment_id]:
                self.active_connections[deployment_id].remove(websocket)
                logger.info(f"WebSocket disconnected from deployment {deployment_id}")
            
            # Clean up empty lists
            if not self.active_connections[deployment_id]:
                del self.active_connections[deployment_id]
    
    async def send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send message to a specific WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            message: Message dict to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
    
    async def broadcast(self, deployment_id: str, message: Dict[str, Any]):
        """
        Broadcast message to all connections for a deployment
        
        Args:
            deployment_id: The deployment to broadcast to
            message: Message dict to broadcast
        """
        if deployment_id not in self.active_connections:
            logger.warning(f"No active connections for deployment {deployment_id}")
            return
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
        
        # Send to all connections
        disconnected = []
        for websocket in self.active_connections[deployment_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected WebSockets
        for websocket in disconnected:
            self.disconnect(deployment_id, websocket)
        
        logger.debug(f"Broadcasted message to {len(self.active_connections.get(deployment_id, []))} connections")
    
    async def send_progress(
        self,
        deployment_id: str,
        percentage: int,
        step: str,
        level: str = "info",
        message: str = None
    ):
        """
        Send progress update
        
        Args:
            deployment_id: The deployment ID
            percentage: Progress percentage (0-100)
            step: Current step name
            level: Message level (info, warning, error, success)
            message: Optional detailed message
        """
        await self.broadcast(deployment_id, {
            "type": "progress",
            "data": {
                "status": "provisioning" if percentage < 100 else "complete",
                "percentage": percentage,
                "step": step,
                "level": level,
                "message": message or step
            }
        })
    
    async def send_log(
        self,
        deployment_id: str,
        level: str,
        message: str,
        step: str = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Send log message
        
        Args:
            deployment_id: The deployment ID
            level: Log level (info, warning, error, success)
            message: Log message
            step: Optional step name
            metadata: Optional additional data
        """
        await self.broadcast(deployment_id, {
            "type": "log",
            "level": level,
            "message": message,
            "step": step,
            "metadata": metadata or {}
        })
    
    async def send_completion(
        self,
        deployment_id: str,
        result: Dict[str, Any]
    ):
        """
        Send deployment completion message
        
        Args:
            deployment_id: The deployment ID
            result: Deployment result data
        """
        await self.broadcast(deployment_id, {
            "type": "complete",
            "data": result
        })
    
    async def send_error(
        self,
        deployment_id: str,
        error: str,
        step: str = None
    ):
        """
        Send error message
        
        Args:
            deployment_id: The deployment ID
            error: Error message
            step: Optional step where error occurred
        """
        await self.broadcast(deployment_id, {
            "type": "error",
            "error": error,
            "step": step
        })
    
    def get_connection_count(self, deployment_id: str) -> int:
        """
        Get number of active connections for a deployment
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(deployment_id, []))
    
    def get_total_connections(self) -> int:
        """
        Get total number of active connections across all deployments
        
        Returns:
            Total number of connections
        """
        return sum(len(connections) for connections in self.active_connections.values())
    
    async def close_all(self, deployment_id: str):
        """
        Close all WebSocket connections for a deployment
        
        Args:
            deployment_id: The deployment ID
        """
        if deployment_id in self.active_connections:
            for websocket in self.active_connections[deployment_id]:
                try:
                    await websocket.close()
                except Exception as e:
                    logger.error(f"Error closing WebSocket: {e}")
            
            del self.active_connections[deployment_id]
            logger.info(f"Closed all WebSocket connections for deployment {deployment_id}")


# Global manager instance
_ws_manager = None


def get_websocket_manager() -> DeploymentWebSocketManager:
    """Get or create global WebSocket manager instance"""
    global _ws_manager
    
    if _ws_manager is None:
        _ws_manager = DeploymentWebSocketManager()
    
    return _ws_manager
