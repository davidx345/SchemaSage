"""
WebSocket connection management for real-time collaboration
"""
import asyncio
import json
import logging
import websockets
from websockets.server import WebSocketServerProtocol
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid

from .models import (
    CollaborationUser, CollaborationEvent, CollaborationEventType,
    CollaborationSession, PresenceInfo, UserRole, CollaborationError,
    UserNotFoundError, SessionFullError
)

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time collaboration"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.session_connections: Dict[str, Set[str]] = {}  # session_id -> set of user_ids
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
    
    async def add_connection(
        self,
        websocket: WebSocketServerProtocol,
        user_id: str,
        session_id: str
    ) -> bool:
        """Add a new WebSocket connection"""
        try:
            # Store connection
            self.connections[user_id] = websocket
            self.user_sessions[user_id] = session_id
            
            # Add to session connections
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(user_id)
            
            # Start heartbeat
            await self._start_heartbeat(user_id)
            
            logger.info(f"WebSocket connection added for user {user_id} in session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add WebSocket connection: {str(e)}")
            return False
    
    async def remove_connection(self, user_id: str) -> bool:
        """Remove a WebSocket connection"""
        try:
            # Stop heartbeat
            await self._stop_heartbeat(user_id)
            
            # Get session ID before removing
            session_id = self.user_sessions.get(user_id)
            
            # Remove from connections
            if user_id in self.connections:
                del self.connections[user_id]
            
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            
            # Remove from session connections
            if session_id and session_id in self.session_connections:
                self.session_connections[session_id].discard(user_id)
                
                # Clean up empty sessions
                if not self.session_connections[session_id]:
                    del self.session_connections[session_id]
            
            logger.info(f"WebSocket connection removed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove WebSocket connection: {str(e)}")
            return False
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific user"""
        try:
            if user_id not in self.connections:
                logger.warning(f"No connection found for user {user_id}")
                return False
            
            websocket = self.connections[user_id]
            message_str = json.dumps(message)
            
            await websocket.send(message_str)
            return True
            
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed for user {user_id}")
            await self.remove_connection(user_id)
            return False
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {str(e)}")
            return False
    
    async def broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any],
        exclude_user: Optional[str] = None
    ) -> int:
        """Broadcast message to all users in session"""
        sent_count = 0
        
        if session_id not in self.session_connections:
            logger.warning(f"No connections found for session {session_id}")
            return sent_count
        
        user_ids = self.session_connections[session_id].copy()
        
        for user_id in user_ids:
            if exclude_user and user_id == exclude_user:
                continue
            
            success = await self.send_to_user(user_id, message)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all connected users"""
        sent_count = 0
        
        user_ids = list(self.connections.keys())
        
        for user_id in user_ids:
            success = await self.send_to_user(user_id, message)
            if success:
                sent_count += 1
        
        return sent_count
    
    def get_session_users(self, session_id: str) -> Set[str]:
        """Get all users connected to a session"""
        return self.session_connections.get(session_id, set()).copy()
    
    def get_user_session(self, user_id: str) -> Optional[str]:
        """Get session ID for a user"""
        return self.user_sessions.get(user_id)
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if user is connected"""
        return user_id in self.connections
    
    def get_connection_count(self) -> int:
        """Get total number of connections"""
        return len(self.connections)
    
    def get_session_connection_count(self, session_id: str) -> int:
        """Get number of connections in a session"""
        return len(self.session_connections.get(session_id, set()))
    
    async def _start_heartbeat(self, user_id: str):
        """Start heartbeat for a user connection"""
        async def heartbeat():
            try:
                while user_id in self.connections:
                    await asyncio.sleep(self.heartbeat_interval)
                    
                    # Send ping
                    ping_message = {
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    success = await self.send_to_user(user_id, ping_message)
                    if not success:
                        break
                        
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Heartbeat error for user {user_id}: {str(e)}")
        
        # Cancel existing heartbeat if any
        await self._stop_heartbeat(user_id)
        
        # Start new heartbeat
        self.heartbeat_tasks[user_id] = asyncio.create_task(heartbeat())
    
    async def _stop_heartbeat(self, user_id: str):
        """Stop heartbeat for a user"""
        if user_id in self.heartbeat_tasks:
            task = self.heartbeat_tasks[user_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self.heartbeat_tasks[user_id]
    
    async def cleanup(self):
        """Clean up all connections and tasks"""
        # Stop all heartbeats
        for user_id in list(self.heartbeat_tasks.keys()):
            await self._stop_heartbeat(user_id)
        
        # Close all connections
        for user_id, websocket in list(self.connections.items()):
            try:
                await websocket.close()
            except:
                pass
        
        # Clear all data
        self.connections.clear()
        self.user_sessions.clear()
        self.session_connections.clear()

class MessageHandler:
    """Handles incoming WebSocket messages"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.message_handlers = {
            "join_session": self._handle_join_session,
            "leave_session": self._handle_leave_session,
            "schema_update": self._handle_schema_update,
            "cursor_move": self._handle_cursor_move,
            "selection_change": self._handle_selection_change,
            "typing_start": self._handle_typing_start,
            "typing_stop": self._handle_typing_stop,
            "comment_add": self._handle_comment_add,
            "lock_request": self._handle_lock_request,
            "lock_release": self._handle_lock_release,
            "pong": self._handle_pong
        }
    
    async def handle_message(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle incoming WebSocket message"""
        try:
            message_type = message.get("type")
            
            if message_type not in self.message_handlers:
                return {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }
            
            handler = self.message_handlers[message_type]
            return await handler(websocket, message, user_id)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return {
                "type": "error",
                "message": f"Failed to handle message: {str(e)}"
            }
    
    async def _handle_join_session(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle join session request"""
        session_id = message.get("session_id")
        
        if not session_id:
            return {
                "type": "error",
                "message": "session_id is required"
            }
        
        # Add connection
        success = await self.websocket_manager.add_connection(
            websocket, user_id, session_id
        )
        
        if success:
            # Notify other users
            notification = {
                "type": "user_joined",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket_manager.broadcast_to_session(
                session_id, notification, exclude_user=user_id
            )
            
            return {
                "type": "joined",
                "session_id": session_id,
                "user_id": user_id
            }
        else:
            return {
                "type": "error",
                "message": "Failed to join session"
            }
    
    async def _handle_leave_session(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle leave session request"""
        session_id = self.websocket_manager.get_user_session(user_id)
        
        if session_id:
            # Remove connection
            await self.websocket_manager.remove_connection(user_id)
            
            # Notify other users
            notification = {
                "type": "user_left",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket_manager.broadcast_to_session(
                session_id, notification
            )
        
        return {
            "type": "left",
            "user_id": user_id
        }
    
    async def _handle_schema_update(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle schema update"""
        session_id = self.websocket_manager.get_user_session(user_id)
        
        if not session_id:
            return {
                "type": "error",
                "message": "User not in session"
            }
        
        # Broadcast update to other users
        update_message = {
            "type": "schema_updated",
            "user_id": user_id,
            "data": message.get("data", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, update_message, exclude_user=user_id
        )
        
        return {
            "type": "update_acknowledged",
            "user_id": user_id
        }
    
    async def _handle_cursor_move(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle cursor movement"""
        session_id = self.websocket_manager.get_user_session(user_id)
        
        if not session_id:
            return {
                "type": "error",
                "message": "User not in session"
            }
        
        # Broadcast cursor position
        cursor_message = {
            "type": "cursor_moved",
            "user_id": user_id,
            "position": message.get("position", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, cursor_message, exclude_user=user_id
        )
        
        return {"type": "cursor_acknowledged"}
    
    async def _handle_selection_change(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle selection change"""
        session_id = self.websocket_manager.get_user_session(user_id)
        
        if not session_id:
            return {
                "type": "error",
                "message": "User not in session"
            }
        
        # Broadcast selection
        selection_message = {
            "type": "selection_changed",
            "user_id": user_id,
            "selection": message.get("selection", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, selection_message, exclude_user=user_id
        )
        
        return {"type": "selection_acknowledged"}
    
    async def _handle_typing_start(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle typing start"""
        session_id = self.websocket_manager.get_user_session(user_id)
        
        if not session_id:
            return {
                "type": "error",
                "message": "User not in session"
            }
        
        # Broadcast typing indicator
        typing_message = {
            "type": "user_typing",
            "user_id": user_id,
            "element_id": message.get("element_id"),
            "is_typing": True,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, typing_message, exclude_user=user_id
        )
        
        return {"type": "typing_acknowledged"}
    
    async def _handle_typing_stop(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle typing stop"""
        session_id = self.websocket_manager.get_user_session(user_id)
        
        if not session_id:
            return {
                "type": "error",
                "message": "User not in session"
            }
        
        # Broadcast typing stop
        typing_message = {
            "type": "user_typing",
            "user_id": user_id,
            "element_id": message.get("element_id"),
            "is_typing": False,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, typing_message, exclude_user=user_id
        )
        
        return {"type": "typing_acknowledged"}
    
    async def _handle_comment_add(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle comment addition"""
        session_id = self.websocket_manager.get_user_session(user_id)
        
        if not session_id:
            return {
                "type": "error",
                "message": "User not in session"
            }
        
        # Broadcast comment
        comment_message = {
            "type": "comment_added",
            "user_id": user_id,
            "comment": message.get("comment", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, comment_message, exclude_user=user_id
        )
        
        return {"type": "comment_acknowledged"}
    
    async def _handle_lock_request(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle lock request"""
        session_id = self.websocket_manager.get_user_session(user_id)
        
        if not session_id:
            return {
                "type": "error",
                "message": "User not in session"
            }
        
        # This would typically involve checking with the collaboration engine
        # For now, just broadcast the lock request
        lock_message = {
            "type": "lock_requested",
            "user_id": user_id,
            "element_id": message.get("element_id"),
            "lock_type": message.get("lock_type"),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, lock_message, exclude_user=user_id
        )
        
        return {"type": "lock_acknowledged"}
    
    async def _handle_lock_release(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle lock release"""
        session_id = self.websocket_manager.get_user_session(user_id)
        
        if not session_id:
            return {
                "type": "error",
                "message": "User not in session"
            }
        
        # Broadcast lock release
        release_message = {
            "type": "lock_released",
            "user_id": user_id,
            "element_id": message.get("element_id"),
            "lock_type": message.get("lock_type"),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, release_message, exclude_user=user_id
        )
        
        return {"type": "release_acknowledged"}
    
    async def _handle_pong(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle pong response to ping"""
        # Just acknowledge - the connection is alive
        return {"type": "pong_acknowledged"}
