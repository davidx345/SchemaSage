"""
Real-time collaboration module initialization
"""

from .models import (
    CollaborationEventType,
    UserRole,
    LockType,
    ConflictResolutionStrategy,
    CollaborationUser,
    CollaborationEvent,
    ElementLock,
    ConflictInfo,
    Comment,
    CursorPosition,
    Selection,
    PresenceInfo,
    SessionPermissions,
    CollaborationSession,
    CollaborationError,
    UserNotFoundError,
    PermissionDeniedError,
    ElementLockedError,
    ConflictError,
    SessionFullError,
    get_user_permissions,
    generate_user_color,
    is_valid_event_type,
    create_event
)

from .websocket_manager import (
    WebSocketManager,
    MessageHandler
)

from .collaboration_engine import CollaborationEngine

__all__ = [
    # Models and types
    "CollaborationEventType",
    "UserRole",
    "LockType", 
    "ConflictResolutionStrategy",
    "CollaborationUser",
    "CollaborationEvent",
    "ElementLock",
    "ConflictInfo",
    "Comment",
    "CursorPosition",
    "Selection",
    "PresenceInfo",
    "SessionPermissions",
    "CollaborationSession",
    
    # Exceptions
    "CollaborationError",
    "UserNotFoundError",
    "PermissionDeniedError",
    "ElementLockedError",
    "ConflictError",
    "SessionFullError",
    
    # Utility functions
    "get_user_permissions",
    "generate_user_color",
    "is_valid_event_type",
    "create_event",
    
    # Core classes
    "WebSocketManager",
    "MessageHandler",
    "CollaborationEngine",
    
    # Main service class
    "RealTimeCollaborationService"
]

class RealTimeCollaborationService:
    """
    Main service class for real-time collaboration functionality
    Orchestrates WebSocket management and collaboration engine
    """
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.collaboration_engine = CollaborationEngine(self.websocket_manager)
        self.message_handler = MessageHandler(self.websocket_manager)
        self.is_running = False
    
    async def start(self):
        """Start the collaboration service"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Real-time collaboration service started")
    
    async def stop(self):
        """Stop the collaboration service"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cleanup resources
        await self.collaboration_engine.cleanup()
        await self.websocket_manager.cleanup()
        
        logger.info("Real-time collaboration service stopped")
    
    async def create_session(
        self,
        schema_id: str,
        name: str,
        owner_id: str,
        description: str = "",
        max_users: int = 10
    ) -> CollaborationSession:
        """
        Create a new collaboration session
        
        Args:
            schema_id: ID of the schema to collaborate on
            name: Name of the collaboration session
            owner_id: ID of the session owner
            description: Optional description
            max_users: Maximum number of users allowed
            
        Returns:
            Created collaboration session
        """
        return await self.collaboration_engine.create_session(
            schema_id, name, owner_id, description, max_users
        )
    
    async def join_session(
        self,
        session_id: str,
        user_id: str,
        username: str,
        email: str,
        role: UserRole = UserRole.EDITOR
    ) -> CollaborationUser:
        """
        Add user to collaboration session
        
        Args:
            session_id: ID of the session to join
            user_id: ID of the user
            username: Display name of the user
            email: Email of the user
            role: Role of the user in the session
            
        Returns:
            Collaboration user object
        """
        return await self.collaboration_engine.join_session(
            session_id, user_id, username, email, role
        )
    
    async def leave_session(self, session_id: str, user_id: str) -> bool:
        """
        Remove user from collaboration session
        
        Args:
            session_id: ID of the session
            user_id: ID of the user to remove
            
        Returns:
            True if user was successfully removed
        """
        return await self.collaboration_engine.leave_session(session_id, user_id)
    
    async def handle_websocket_connection(
        self,
        websocket,
        user_id: str,
        session_id: str
    ):
        """
        Handle WebSocket connection for real-time collaboration
        
        Args:
            websocket: WebSocket connection
            user_id: ID of the connected user
            session_id: ID of the collaboration session
        """
        try:
            # Add WebSocket connection
            await self.websocket_manager.add_connection(websocket, user_id, session_id)
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.message_handler.handle_message(
                        websocket, data, user_id
                    )
                    
                    if response:
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    error_response = {
                        "type": "error",
                        "message": "Invalid JSON message"
                    }
                    await websocket.send(json.dumps(error_response))
                    
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")
                    error_response = {
                        "type": "error", 
                        "message": f"Message handling failed: {str(e)}"
                    }
                    await websocket.send(json.dumps(error_response))
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            
        finally:
            # Clean up connection
            await self.websocket_manager.remove_connection(user_id)
            await self.collaboration_engine.leave_session(session_id, user_id)
    
    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get collaboration session by ID"""
        return self.collaboration_engine.get_session(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[CollaborationSession]:
        """Get all sessions user is part of"""
        return self.collaboration_engine.get_user_sessions(user_id)
    
    async def update_schema(
        self,
        session_id: str,
        user_id: str,
        update_data: Dict[str, Any],
        affected_elements: List[str] = None
    ) -> bool:
        """
        Handle schema update from user
        
        Args:
            session_id: ID of the collaboration session
            user_id: ID of the user making the update
            update_data: Data describing the update
            affected_elements: List of element IDs affected by the update
            
        Returns:
            True if update was successful
        """
        return await self.collaboration_engine.update_schema(
            session_id, user_id, update_data, affected_elements
        )
    
    async def acquire_lock(
        self,
        session_id: str,
        user_id: str,
        element_id: str,
        element_type: str,
        lock_type: LockType = LockType.TABLE_LOCK,
        is_exclusive: bool = True,
        timeout_minutes: int = 5
    ) -> ElementLock:
        """
        Acquire lock on schema element
        
        Args:
            session_id: ID of the collaboration session
            user_id: ID of the user requesting the lock
            element_id: ID of the element to lock
            element_type: Type of the element (table, column, etc.)
            lock_type: Type of lock to acquire
            is_exclusive: Whether the lock is exclusive
            timeout_minutes: Lock timeout in minutes
            
        Returns:
            Created element lock
        """
        return await self.collaboration_engine.acquire_lock(
            session_id, user_id, element_id, element_type,
            lock_type, is_exclusive, timeout_minutes
        )
    
    async def release_lock(
        self,
        session_id: str,
        user_id: str,
        lock_id: str
    ) -> bool:
        """
        Release a specific lock
        
        Args:
            session_id: ID of the collaboration session
            user_id: ID of the user releasing the lock
            lock_id: ID of the lock to release
            
        Returns:
            True if lock was successfully released
        """
        return await self.collaboration_engine.release_lock(
            session_id, user_id, lock_id
        )
    
    async def add_comment(
        self,
        session_id: str,
        user_id: str,
        element_id: str,
        element_type: str,
        content: str
    ) -> Comment:
        """
        Add comment to schema element
        
        Args:
            session_id: ID of the collaboration session
            user_id: ID of the user adding the comment
            element_id: ID of the element to comment on
            element_type: Type of the element
            content: Comment content
            
        Returns:
            Created comment
        """
        return await self.collaboration_engine.add_comment(
            session_id, user_id, element_id, element_type, content
        )
    
    async def update_presence(
        self,
        session_id: str,
        user_id: str,
        cursor_position: Optional[Dict[str, Any]] = None,
        selection: Optional[Dict[str, Any]] = None,
        current_view: Optional[str] = None,
        is_typing: bool = False,
        typing_element: Optional[str] = None
    ) -> bool:
        """
        Update user presence information
        
        Args:
            session_id: ID of the collaboration session
            user_id: ID of the user
            cursor_position: Current cursor position
            selection: Current selection
            current_view: Current view/section being viewed
            is_typing: Whether user is currently typing
            typing_element: Element user is typing in
            
        Returns:
            True if presence was successfully updated
        """
        return await self.collaboration_engine.update_presence(
            session_id, user_id, cursor_position, selection,
            current_view, is_typing, typing_element
        )
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a collaboration session
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dictionary containing session statistics
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        active_users = sum(1 for user in session.users.values() if user.is_active)
        online_users = sum(1 for presence in session.presence.values() if presence.is_online)
        
        return {
            "session_id": session_id,
            "total_users": len(session.users),
            "active_users": active_users,
            "online_users": online_users,
            "total_events": len(session.event_history),
            "active_locks": len(session.locks),
            "unresolved_conflicts": len([c for c in session.conflicts.values() if not c.resolved]),
            "total_comments": len(session.comments),
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "is_active": session.is_active
        }

# Create logger for the module
import logging
logger = logging.getLogger(__name__)
