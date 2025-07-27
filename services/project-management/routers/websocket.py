"""
WebSocket API Routes

Routes for real-time features including schema editing collaboration.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)

# Router for WebSocket endpoints
router = APIRouter(tags=["websocket"])

# Store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        """Connect a WebSocket to a project room"""
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        logger.info(f"WebSocket connected to project {project_id}")
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        """Disconnect a WebSocket from a project room"""
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        logger.info(f"WebSocket disconnected from project {project_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a personal message to a specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_project(self, message: str, project_id: str, exclude_websocket: WebSocket = None):
        """Broadcast a message to all WebSockets in a project room"""
        if project_id not in self.active_connections:
            return
        
        disconnected = []
        for websocket in self.active_connections[project_id]:
            if websocket == exclude_websocket:
                continue
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected WebSockets
        for ws in disconnected:
            self.disconnect(ws, project_id)


manager = ConnectionManager()


@router.websocket("/ws/schema-edit/{project_id}")
async def websocket_schema_edit(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for collaborative schema editing"""
    await manager.connect(websocket, project_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": f"Connected to project {project_id}",
                "project_id": project_id
            }),
            websocket
        )
        
        while True:
            # Receive message from WebSocket
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                logger.info(f"Received WebSocket message: {message_type} for project {project_id}")
                
                # Handle different message types
                if message_type == "schema_change":
                    # Broadcast schema changes to other users
                    await manager.broadcast_to_project(
                        json.dumps({
                            "type": "schema_change",
                            "project_id": project_id,
                            "user": message.get("user", "anonymous"),
                            "changes": message.get("changes", {}),
                            "timestamp": message.get("timestamp")
                        }),
                        project_id,
                        exclude_websocket=websocket
                    )
                    
                    # Send acknowledgment back to sender
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "ack",
                            "message": "Schema change broadcasted",
                            "original_type": message_type
                        }),
                        websocket
                    )
                
                elif message_type == "cursor_position":
                    # Broadcast cursor position to other users
                    await manager.broadcast_to_project(
                        json.dumps({
                            "type": "cursor_position",
                            "project_id": project_id,
                            "user": message.get("user", "anonymous"),
                            "position": message.get("position", {}),
                            "timestamp": message.get("timestamp")
                        }),
                        project_id,
                        exclude_websocket=websocket
                    )
                
                elif message_type == "user_join":
                    # Notify others that a user joined
                    await manager.broadcast_to_project(
                        json.dumps({
                            "type": "user_join",
                            "project_id": project_id,
                            "user": message.get("user", "anonymous"),
                            "timestamp": message.get("timestamp")
                        }),
                        project_id,
                        exclude_websocket=websocket
                    )
                
                elif message_type == "user_leave":
                    # Notify others that a user left
                    await manager.broadcast_to_project(
                        json.dumps({
                            "type": "user_leave",
                            "project_id": project_id,
                            "user": message.get("user", "anonymous"),
                            "timestamp": message.get("timestamp")
                        }),
                        project_id,
                        exclude_websocket=websocket
                    )
                
                elif message_type == "comment":
                    # Broadcast comments to other users
                    await manager.broadcast_to_project(
                        json.dumps({
                            "type": "comment",
                            "project_id": project_id,
                            "user": message.get("user", "anonymous"),
                            "comment": message.get("comment", ""),
                            "target": message.get("target", {}),  # What the comment is about
                            "timestamp": message.get("timestamp")
                        }),
                        project_id,
                        exclude_websocket=websocket
                    )
                
                elif message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": message.get("timestamp")
                        }),
                        websocket
                    )
                
                else:
                    # Unknown message type
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        }),
                        websocket
                    )
            
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }),
                    websocket
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Error processing message"
                    }),
                    websocket
                )
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from project {project_id}")
    except Exception as e:
        logger.error(f"WebSocket error for project {project_id}: {e}")
    finally:
        manager.disconnect(websocket, project_id)


@router.get("/ws/status/{project_id}")
async def get_websocket_status(project_id: str):
    """Get the status of WebSocket connections for a project"""
    connections = manager.active_connections.get(project_id, [])
    return {
        "project_id": project_id,
        "active_connections": len(connections),
        "status": "active" if connections else "inactive"
    }


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get overall WebSocket connection statistics"""
    total_connections = sum(len(conns) for conns in manager.active_connections.values())
    return {
        "total_projects": len(manager.active_connections),
        "total_connections": total_connections,
        "projects": {
            project_id: len(conns) 
            for project_id, conns in manager.active_connections.items()
        }
    }
