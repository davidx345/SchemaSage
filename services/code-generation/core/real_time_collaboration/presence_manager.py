"""
Presence management for real-time collaboration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

from .models import (
    PresenceInfo,
    CollaborationUser,
    CursorPosition,
    Selection
)

logger = logging.getLogger(__name__)


@dataclass
class UserActivity:
    """Track user activity for presence management"""
    user_id: str
    last_seen: datetime
    last_action: datetime
    session_start: datetime
    actions_count: int = 0
    is_typing: bool = False
    typing_element: Optional[str] = None
    current_view: Optional[str] = None
    active_elements: Set[str] = field(default_factory=set)


class PresenceManager:
    """
    Manages user presence and activity tracking in collaboration sessions
    """
    
    def __init__(self):
        self.user_activities: Dict[str, UserActivity] = {}
        self.presence_data: Dict[str, PresenceInfo] = {}
        self.session_users: Dict[str, Set[str]] = {}  # session_id -> user_ids
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        self.activity_timeout = timedelta(minutes=5)
        self.presence_timeout = timedelta(minutes=1)
        self.cleanup_interval = 60  # seconds
        self._cleanup_task = None
        self._running = False
    
    async def start(self):
        """Start the presence manager"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Presence manager started")
    
    async def stop(self):
        """Stop the presence manager"""
        if not self._running:
            return
        
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Presence manager stopped")
    
    async def user_joined_session(self, session_id: str, user: CollaborationUser):
        """
        Handle user joining a collaboration session
        
        Args:
            session_id: ID of the session
            user: User who joined
        """
        user_id = user.user_id
        now = datetime.utcnow()
        
        # Initialize user activity
        if user_id not in self.user_activities:
            self.user_activities[user_id] = UserActivity(
                user_id=user_id,
                last_seen=now,
                last_action=now,
                session_start=now
            )
        else:
            # Update existing activity
            self.user_activities[user_id].last_seen = now
            self.user_activities[user_id].last_action = now
        
        # Initialize presence info
        presence_key = f"{session_id}:{user_id}"
        self.presence_data[presence_key] = PresenceInfo(
            user_id=user_id,
            username=user.username,
            color=user.color,
            is_online=True,
            last_seen=now,
            cursor_position=None,
            selection=None,
            current_view=None,
            is_typing=False,
            typing_element=None
        )
        
        # Track session membership
        if session_id not in self.session_users:
            self.session_users[session_id] = set()
        self.session_users[session_id].add(user_id)
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        logger.info(f"User {user_id} joined session {session_id}")
    
    async def user_left_session(self, session_id: str, user_id: str):
        """
        Handle user leaving a collaboration session
        
        Args:
            session_id: ID of the session
            user_id: ID of the user who left
        """
        # Update presence to offline
        presence_key = f"{session_id}:{user_id}"
        if presence_key in self.presence_data:
            self.presence_data[presence_key].is_online = False
            self.presence_data[presence_key].last_seen = datetime.utcnow()
        
        # Remove from session tracking
        if session_id in self.session_users:
            self.session_users[session_id].discard(user_id)
            
            # Clean up empty sessions
            if not self.session_users[session_id]:
                del self.session_users[session_id]
        
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)
            
            # Clean up if user has no active sessions
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
                if user_id in self.user_activities:
                    del self.user_activities[user_id]
        
        logger.info(f"User {user_id} left session {session_id}")
    
    async def update_user_presence(
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
        presence_key = f"{session_id}:{user_id}"
        now = datetime.utcnow()
        
        # Update user activity
        if user_id in self.user_activities:
            activity = self.user_activities[user_id]
            activity.last_seen = now
            activity.last_action = now
            activity.actions_count += 1
            activity.is_typing = is_typing
            activity.typing_element = typing_element
            activity.current_view = current_view
        
        # Update presence info
        if presence_key in self.presence_data:
            presence = self.presence_data[presence_key]
            presence.last_seen = now
            presence.is_online = True
            
            # Update cursor position
            if cursor_position:
                presence.cursor_position = CursorPosition(
                    x=cursor_position.get("x", 0),
                    y=cursor_position.get("y", 0),
                    element_id=cursor_position.get("element_id"),
                    element_type=cursor_position.get("element_type")
                )
            
            # Update selection
            if selection:
                presence.selection = Selection(
                    start_x=selection.get("start_x", 0),
                    start_y=selection.get("start_y", 0),
                    end_x=selection.get("end_x", 0),
                    end_y=selection.get("end_y", 0),
                    element_id=selection.get("element_id"),
                    element_type=selection.get("element_type")
                )
            
            presence.current_view = current_view
            presence.is_typing = is_typing
            presence.typing_element = typing_element
            
            return True
        
        return False
    
    async def update_user_activity(self, user_id: str, action_type: str = "general"):
        """
        Update user activity timestamp
        
        Args:
            user_id: ID of the user
            action_type: Type of action performed
        """
        if user_id in self.user_activities:
            activity = self.user_activities[user_id]
            activity.last_action = datetime.utcnow()
            activity.actions_count += 1
            
            # Track active elements based on action type
            if action_type.startswith("element_"):
                element_id = action_type.split("_", 1)[1]
                activity.active_elements.add(element_id)
    
    def get_session_presence(self, session_id: str) -> List[PresenceInfo]:
        """
        Get presence information for all users in a session
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of presence information for session users
        """
        if session_id not in self.session_users:
            return []
        
        presence_list = []
        for user_id in self.session_users[session_id]:
            presence_key = f"{session_id}:{user_id}"
            if presence_key in self.presence_data:
                presence_list.append(self.presence_data[presence_key])
        
        return presence_list
    
    def get_user_presence(self, session_id: str, user_id: str) -> Optional[PresenceInfo]:
        """
        Get presence information for a specific user in a session
        
        Args:
            session_id: ID of the session
            user_id: ID of the user
            
        Returns:
            Presence information or None if not found
        """
        presence_key = f"{session_id}:{user_id}"
        return self.presence_data.get(presence_key)
    
    def get_online_users(self, session_id: str) -> List[str]:
        """
        Get list of online users in a session
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of user IDs who are currently online
        """
        online_users = []
        
        if session_id in self.session_users:
            for user_id in self.session_users[session_id]:
                presence_key = f"{session_id}:{user_id}"
                presence = self.presence_data.get(presence_key)
                
                if presence and presence.is_online:
                    # Check if user is actually active
                    if self._is_user_active(user_id):
                        online_users.append(user_id)
        
        return online_users
    
    def get_typing_users(self, session_id: str, element_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of users currently typing
        
        Args:
            session_id: ID of the session
            element_id: Optional element ID to filter by
            
        Returns:
            List of typing user information
        """
        typing_users = []
        
        if session_id in self.session_users:
            for user_id in self.session_users[session_id]:
                presence_key = f"{session_id}:{user_id}"
                presence = self.presence_data.get(presence_key)
                
                if (presence and presence.is_typing and 
                    (element_id is None or presence.typing_element == element_id)):
                    typing_users.append({
                        "user_id": user_id,
                        "username": presence.username,
                        "typing_element": presence.typing_element,
                        "color": presence.color
                    })
        
        return typing_users
    
    def get_user_statistics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get activity statistics for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary containing user statistics
        """
        if user_id not in self.user_activities:
            return None
        
        activity = self.user_activities[user_id]
        now = datetime.utcnow()
        
        return {
            "user_id": user_id,
            "session_duration": (now - activity.session_start).total_seconds(),
            "last_seen": activity.last_seen.isoformat(),
            "last_action": activity.last_action.isoformat(),
            "actions_count": activity.actions_count,
            "is_typing": activity.is_typing,
            "typing_element": activity.typing_element,
            "current_view": activity.current_view,
            "active_elements": list(activity.active_elements),
            "active_sessions": len(self.user_sessions.get(user_id, set())),
            "is_active": self._is_user_active(user_id)
        }
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Get activity statistics for a session
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dictionary containing session statistics
        """
        if session_id not in self.session_users:
            return {
                "session_id": session_id,
                "total_users": 0,
                "online_users": 0,
                "active_users": 0,
                "typing_users": 0
            }
        
        total_users = len(self.session_users[session_id])
        online_users = len(self.get_online_users(session_id))
        typing_users = len(self.get_typing_users(session_id))
        
        active_users = 0
        for user_id in self.session_users[session_id]:
            if self._is_user_active(user_id):
                active_users += 1
        
        return {
            "session_id": session_id,
            "total_users": total_users,
            "online_users": online_users,
            "active_users": active_users,
            "typing_users": typing_users
        }
    
    async def cleanup_inactive_users(self):
        """Clean up inactive users and stale presence data"""
        now = datetime.utcnow()
        users_to_remove = []
        presence_to_remove = []
        
        # Find inactive users
        for user_id, activity in self.user_activities.items():
            if now - activity.last_seen > self.activity_timeout:
                users_to_remove.append(user_id)
        
        # Find stale presence data
        for presence_key, presence in self.presence_data.items():
            if now - presence.last_seen > self.presence_timeout:
                presence.is_online = False
                
                # Mark for removal if offline for too long
                if now - presence.last_seen > self.activity_timeout:
                    presence_to_remove.append(presence_key)
        
        # Remove inactive users
        for user_id in users_to_remove:
            await self._remove_user(user_id)
        
        # Remove stale presence data
        for presence_key in presence_to_remove:
            if presence_key in self.presence_data:
                del self.presence_data[presence_key]
        
        if users_to_remove or presence_to_remove:
            logger.info(f"Cleaned up {len(users_to_remove)} inactive users and {len(presence_to_remove)} stale presence entries")
    
    async def _remove_user(self, user_id: str):
        """Remove user from all tracking"""
        # Remove from user activities
        if user_id in self.user_activities:
            del self.user_activities[user_id]
        
        # Remove from user sessions
        if user_id in self.user_sessions:
            sessions = self.user_sessions[user_id].copy()
            del self.user_sessions[user_id]
            
            # Remove from session users
            for session_id in sessions:
                if session_id in self.session_users:
                    self.session_users[session_id].discard(user_id)
                    
                    # Clean up empty sessions
                    if not self.session_users[session_id]:
                        del self.session_users[session_id]
        
        # Remove presence data
        presence_keys_to_remove = [
            key for key in self.presence_data.keys() 
            if key.endswith(f":{user_id}")
        ]
        
        for key in presence_keys_to_remove:
            del self.presence_data[key]
    
    def _is_user_active(self, user_id: str) -> bool:
        """Check if user is currently active"""
        if user_id not in self.user_activities:
            return False
        
        activity = self.user_activities[user_id]
        now = datetime.utcnow()
        
        return (now - activity.last_seen) < self.presence_timeout
    
    async def _cleanup_loop(self):
        """Background task for cleaning up inactive users"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                if self._running:
                    await self.cleanup_inactive_users()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in presence cleanup: {str(e)}")
    
    def get_all_active_sessions(self) -> List[str]:
        """Get list of all active session IDs"""
        return list(self.session_users.keys())
    
    def get_user_active_sessions(self, user_id: str) -> List[str]:
        """Get list of active sessions for a user"""
        return list(self.user_sessions.get(user_id, set()))
    
    async def broadcast_presence_update(
        self,
        session_id: str,
        user_id: str,
        event_type: str = "presence_update"
    ) -> Dict[str, Any]:
        """
        Generate presence update event for broadcasting
        
        Args:
            session_id: ID of the session
            user_id: ID of the user whose presence changed
            event_type: Type of presence event
            
        Returns:
            Presence update event data
        """
        presence = self.get_user_presence(session_id, user_id)
        if not presence:
            return {}
        
        return {
            "type": event_type,
            "session_id": session_id,
            "user_id": user_id,
            "presence": {
                "username": presence.username,
                "color": presence.color,
                "is_online": presence.is_online,
                "last_seen": presence.last_seen.isoformat(),
                "cursor_position": presence.cursor_position.__dict__ if presence.cursor_position else None,
                "selection": presence.selection.__dict__ if presence.selection else None,
                "current_view": presence.current_view,
                "is_typing": presence.is_typing,
                "typing_element": presence.typing_element
            },
            "timestamp": datetime.utcnow().isoformat()
        }
