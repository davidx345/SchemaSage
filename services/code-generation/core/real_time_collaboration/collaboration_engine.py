"""
Collaboration engine for managing sessions and operations
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import uuid

from .models import (
    CollaborationUser, CollaborationEvent, CollaborationEventType,
    CollaborationSession, ElementLock, ConflictInfo, Comment,
    PresenceInfo, UserRole, SessionPermissions, LockType,
    ConflictResolutionStrategy, CollaborationError, UserNotFoundError,
    PermissionDeniedError, ElementLockedError, ConflictError,
    SessionFullError, get_user_permissions, generate_user_color,
    create_event
)
from .websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

class CollaborationEngine:
    """Core engine for managing real-time collaboration"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.sessions: Dict[str, CollaborationSession] = {}
        self.lock_timeout = timedelta(minutes=5)  # Default lock timeout
        self.cleanup_interval = 60  # seconds
        self.cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start periodic cleanup task"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                    await self._cleanup_expired_locks()
                    await self._cleanup_inactive_sessions()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Cleanup task error: {str(e)}")
        
        self.cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def create_session(
        self,
        schema_id: str,
        name: str,
        owner_id: str,
        description: str = "",
        max_users: int = 10
    ) -> CollaborationSession:
        """Create a new collaboration session"""
        
        session = CollaborationSession(
            schema_id=schema_id,
            name=name,
            description=description,
            owner_id=owner_id,
            max_users=max_users
        )
        
        # Add owner to session
        owner = CollaborationUser(
            user_id=owner_id,
            username="Owner",  # This should come from user service
            email="",  # This should come from user service
            role=UserRole.OWNER,
            color=generate_user_color(owner_id)
        )
        
        session.users[owner_id] = owner
        session.permissions[owner_id] = get_user_permissions(UserRole.OWNER)
        
        # Store session
        self.sessions[session.session_id] = session
        
        logger.info(f"Created collaboration session {session.session_id} for schema {schema_id}")
        return session
    
    async def join_session(
        self,
        session_id: str,
        user_id: str,
        username: str,
        email: str,
        role: UserRole = UserRole.EDITOR
    ) -> CollaborationUser:
        """Add user to collaboration session"""
        
        if session_id not in self.sessions:
            raise CollaborationError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        # Check if session is full
        if len(session.users) >= session.max_users:
            raise SessionFullError(f"Session {session_id} is full")
        
        # Check if user already in session
        if user_id in session.users:
            user = session.users[user_id]
            user.last_activity = datetime.now()
            user.is_active = True
        else:
            # Create new user
            user = CollaborationUser(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                color=generate_user_color(user_id)
            )
            
            session.users[user_id] = user
            session.permissions[user_id] = get_user_permissions(role)
        
        # Update presence
        session.presence[user_id] = PresenceInfo(
            user_id=user_id,
            is_online=True,
            last_seen=datetime.now()
        )
        
        # Create and broadcast event
        event = create_event(
            CollaborationEventType.USER_JOINED,
            user_id,
            session_id,
            data={
                "username": username,
                "role": role.value,
                "color": user.color
            }
        )
        
        await self._add_event_to_session(session_id, event)
        await self._broadcast_event(session_id, event, exclude_user=user_id)
        
        session.last_activity = datetime.now()
        
        logger.info(f"User {user_id} joined session {session_id}")
        return user
    
    async def leave_session(self, session_id: str, user_id: str) -> bool:
        """Remove user from collaboration session"""
        
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        if user_id not in session.users:
            return False
        
        # Release all locks held by user
        await self._release_user_locks(session_id, user_id)
        
        # Update user status
        user = session.users[user_id]
        user.is_active = False
        user.last_activity = datetime.now()
        
        # Update presence
        if user_id in session.presence:
            session.presence[user_id].is_online = False
            session.presence[user_id].last_seen = datetime.now()
        
        # Create and broadcast event
        event = create_event(
            CollaborationEventType.USER_LEFT,
            user_id,
            session_id,
            data={"username": user.username}
        )
        
        await self._add_event_to_session(session_id, event)
        await self._broadcast_event(session_id, event)
        
        session.last_activity = datetime.now()
        
        logger.info(f"User {user_id} left session {session_id}")
        return True
    
    async def update_schema(
        self,
        session_id: str,
        user_id: str,
        update_data: Dict[str, Any],
        affected_elements: List[str] = None
    ) -> bool:
        """Handle schema update from user"""
        
        if session_id not in self.sessions:
            raise CollaborationError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if user_id not in session.users:
            raise UserNotFoundError(f"User {user_id} not in session")
        
        # Check permissions
        permissions = session.permissions.get(user_id)
        if not permissions or not permissions.can_edit_schema:
            raise PermissionDeniedError("User lacks permission to edit schema")
        
        # Check for locks on affected elements
        if affected_elements:
            locked_elements = await self._check_element_locks(session_id, affected_elements, user_id)
            if locked_elements:
                raise ElementLockedError(f"Elements are locked: {locked_elements}")
        
        # Check for conflicts
        conflicts = await self._detect_conflicts(session_id, user_id, update_data, affected_elements)
        if conflicts:
            await self._handle_conflicts(session_id, conflicts)
        
        # Create and broadcast event
        event = create_event(
            CollaborationEventType.SCHEMA_UPDATED,
            user_id,
            session_id,
            data=update_data,
            affected_elements=affected_elements or []
        )
        
        await self._add_event_to_session(session_id, event)
        await self._broadcast_event(session_id, event, exclude_user=user_id)
        
        session.last_activity = datetime.now()
        session.users[user_id].last_activity = datetime.now()
        
        return True
    
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
        """Acquire lock on schema element"""
        
        if session_id not in self.sessions:
            raise CollaborationError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if user_id not in session.users:
            raise UserNotFoundError(f"User {user_id} not in session")
        
        # Check permissions
        permissions = session.permissions.get(user_id)
        if not permissions or not permissions.can_lock_elements:
            raise PermissionDeniedError("User lacks permission to acquire locks")
        
        # Check existing locks
        existing_lock = self._find_element_lock(session_id, element_id)
        if existing_lock and existing_lock.user_id != user_id and existing_lock.is_exclusive:
            raise ElementLockedError(f"Element {element_id} is already locked by {existing_lock.user_id}")
        
        # Create lock
        lock = ElementLock(
            element_id=element_id,
            element_type=element_type,
            lock_type=lock_type,
            user_id=user_id,
            is_exclusive=is_exclusive,
            expires_at=datetime.now() + timedelta(minutes=timeout_minutes)
        )
        
        session.locks[lock.lock_id] = lock
        
        # Create and broadcast event
        event = create_event(
            CollaborationEventType.LOCK_ACQUIRED,
            user_id,
            session_id,
            data={
                "element_id": element_id,
                "element_type": element_type,
                "lock_type": lock_type.value,
                "is_exclusive": is_exclusive,
                "expires_at": lock.expires_at.isoformat()
            }
        )
        
        await self._add_event_to_session(session_id, event)
        await self._broadcast_event(session_id, event, exclude_user=user_id)
        
        logger.info(f"Lock acquired by {user_id} on {element_id} in session {session_id}")
        return lock
    
    async def release_lock(
        self,
        session_id: str,
        user_id: str,
        lock_id: str
    ) -> bool:
        """Release a specific lock"""
        
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        if lock_id not in session.locks:
            return False
        
        lock = session.locks[lock_id]
        
        # Only lock owner can release, unless user is admin/owner
        user_role = session.users.get(user_id, {}).role if user_id in session.users else None
        if lock.user_id != user_id and user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise PermissionDeniedError("Only lock owner can release lock")
        
        # Remove lock
        del session.locks[lock_id]
        
        # Create and broadcast event
        event = create_event(
            CollaborationEventType.LOCK_RELEASED,
            user_id,
            session_id,
            data={
                "element_id": lock.element_id,
                "element_type": lock.element_type,
                "lock_type": lock.lock_type.value,
                "original_owner": lock.user_id
            }
        )
        
        await self._add_event_to_session(session_id, event)
        await self._broadcast_event(session_id, event)
        
        logger.info(f"Lock {lock_id} released by {user_id} in session {session_id}")
        return True
    
    async def add_comment(
        self,
        session_id: str,
        user_id: str,
        element_id: str,
        element_type: str,
        content: str
    ) -> Comment:
        """Add comment to schema element"""
        
        if session_id not in self.sessions:
            raise CollaborationError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if user_id not in session.users:
            raise UserNotFoundError(f"User {user_id} not in session")
        
        # Check permissions
        permissions = session.permissions.get(user_id)
        if not permissions or not permissions.can_comment:
            raise PermissionDeniedError("User lacks permission to add comments")
        
        # Create comment
        comment = Comment(
            element_id=element_id,
            element_type=element_type,
            user_id=user_id,
            content=content
        )
        
        session.comments[comment.comment_id] = comment
        
        # Create and broadcast event
        event = create_event(
            CollaborationEventType.COMMENT_ADDED,
            user_id,
            session_id,
            data={
                "comment_id": comment.comment_id,
                "element_id": element_id,
                "element_type": element_type,
                "content": content,
                "username": session.users[user_id].username
            }
        )
        
        await self._add_event_to_session(session_id, event)
        await self._broadcast_event(session_id, event, exclude_user=user_id)
        
        session.last_activity = datetime.now()
        
        logger.info(f"Comment added by {user_id} on {element_id} in session {session_id}")
        return comment
    
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
        """Update user presence information"""
        
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        if user_id not in session.users:
            return False
        
        # Update presence
        if user_id not in session.presence:
            session.presence[user_id] = PresenceInfo(user_id=user_id)
        
        presence = session.presence[user_id]
        presence.is_online = True
        presence.last_seen = datetime.now()
        presence.current_view = current_view
        presence.is_typing = is_typing
        presence.typing_element = typing_element
        
        # Update user activity
        session.users[user_id].last_activity = datetime.now()
        
        # Broadcast presence update
        presence_message = {
            "type": "presence_updated",
            "user_id": user_id,
            "presence": {
                "is_online": presence.is_online,
                "current_view": presence.current_view,
                "cursor_position": cursor_position,
                "selection": selection,
                "is_typing": presence.is_typing,
                "typing_element": presence.typing_element
            },
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, presence_message, exclude_user=user_id
        )
        
        return True
    
    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get collaboration session"""
        return self.sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[CollaborationSession]:
        """Get all sessions user is part of"""
        user_sessions = []
        
        for session in self.sessions.values():
            if user_id in session.users and session.users[user_id].is_active:
                user_sessions.append(session)
        
        return user_sessions
    
    async def _add_event_to_session(self, session_id: str, event: CollaborationEvent):
        """Add event to session history"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.event_history.append(event)
            
            # Limit history size
            max_history = 1000
            if len(session.event_history) > max_history:
                session.event_history = session.event_history[-max_history:]
    
    async def _broadcast_event(
        self,
        session_id: str,
        event: CollaborationEvent,
        exclude_user: Optional[str] = None
    ):
        """Broadcast event to session users"""
        message = {
            "type": "collaboration_event",
            "event": {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "affected_elements": event.affected_elements
            }
        }
        
        await self.websocket_manager.broadcast_to_session(
            session_id, message, exclude_user
        )
    
    def _find_element_lock(self, session_id: str, element_id: str) -> Optional[ElementLock]:
        """Find existing lock for element"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        for lock in session.locks.values():
            if lock.element_id == element_id and not self._is_lock_expired(lock):
                return lock
        
        return None
    
    def _is_lock_expired(self, lock: ElementLock) -> bool:
        """Check if lock is expired"""
        if lock.expires_at is None:
            return False
        
        return datetime.now() > lock.expires_at
    
    async def _check_element_locks(
        self,
        session_id: str,
        element_ids: List[str],
        user_id: str
    ) -> List[str]:
        """Check which elements are locked by other users"""
        locked_elements = []
        
        for element_id in element_ids:
            lock = self._find_element_lock(session_id, element_id)
            if lock and lock.user_id != user_id and lock.is_exclusive:
                locked_elements.append(element_id)
        
        return locked_elements
    
    async def _detect_conflicts(
        self,
        session_id: str,
        user_id: str,
        update_data: Dict[str, Any],
        affected_elements: List[str]
    ) -> List[ConflictInfo]:
        """Detect potential conflicts"""
        # This is a simplified conflict detection
        # In practice, this would be more sophisticated
        conflicts = []
        
        # For now, just return empty list
        # Real implementation would check for concurrent edits
        
        return conflicts
    
    async def _handle_conflicts(self, session_id: str, conflicts: List[ConflictInfo]):
        """Handle detected conflicts"""
        for conflict in conflicts:
            # Store conflict in session
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.conflicts[conflict.conflict_id] = conflict
                
                # Broadcast conflict notification
                conflict_event = create_event(
                    CollaborationEventType.CONFLICT_DETECTED,
                    "system",
                    session_id,
                    data={
                        "conflict_id": conflict.conflict_id,
                        "element_id": conflict.element_id,
                        "conflicting_users": conflict.conflicting_users
                    }
                )
                
                await self._broadcast_event(session_id, conflict_event)
    
    async def _release_user_locks(self, session_id: str, user_id: str):
        """Release all locks held by user"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        user_locks = [
            lock_id for lock_id, lock in session.locks.items()
            if lock.user_id == user_id
        ]
        
        for lock_id in user_locks:
            await self.release_lock(session_id, user_id, lock_id)
    
    async def _cleanup_expired_locks(self):
        """Clean up expired locks"""
        for session_id, session in self.sessions.items():
            expired_locks = [
                lock_id for lock_id, lock in session.locks.items()
                if self._is_lock_expired(lock)
            ]
            
            for lock_id in expired_locks:
                lock = session.locks[lock_id]
                del session.locks[lock_id]
                
                # Broadcast lock expiration
                event = create_event(
                    CollaborationEventType.LOCK_RELEASED,
                    "system",
                    session_id,
                    data={
                        "element_id": lock.element_id,
                        "reason": "expired",
                        "original_owner": lock.user_id
                    }
                )
                
                await self._broadcast_event(session_id, event)
    
    async def _cleanup_inactive_sessions(self):
        """Clean up inactive sessions"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        inactive_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.last_activity < cutoff_time and not any(
                user.is_active for user in session.users.values()
            )
        ]
        
        for session_id in inactive_sessions:
            logger.info(f"Cleaning up inactive session {session_id}")
            del self.sessions[session_id]
    
    async def cleanup(self):
        """Clean up collaboration engine"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
