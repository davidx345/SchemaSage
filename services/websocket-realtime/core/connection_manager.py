"""
WebSocket connection management
"""
from fastapi import WebSocket
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_sessions: Dict[WebSocket, str] = {}
        self.connection_count = 0
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.user_sessions[websocket] = user_id
        self.connection_count += 1
        
        logger.info(f"User {user_id} connected. Total connections: {self.connection_count}")
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.user_sessions:
            user_id = self.user_sessions[websocket]
            
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # Remove user entry if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            del self.user_sessions[websocket]
            self.connection_count -= 1
            
            logger.info(f"User {user_id} disconnected. Total connections: {self.connection_count}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to user {user_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users"""
        message_str = json.dumps(message)
        disconnected = []
        
        for user_id, connections in self.active_connections.items():
            for websocket in connections.copy():
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.warning(f"Failed to broadcast to user {user_id}: {e}")
                    disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_active_user_count(self) -> int:
        """Get number of unique active users"""
        return len(self.active_connections)
    
    def get_total_connection_count(self) -> int:
        """Get total number of active connections"""
        return self.connection_count