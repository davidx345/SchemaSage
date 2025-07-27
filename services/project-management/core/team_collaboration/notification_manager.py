"""
Notification system for team collaboration
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from .models import Notification, NotificationType

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manages notifications for team collaboration events
    """
    
    def __init__(self):
        self.notifications: Dict[str, List[Notification]] = {}  # user_id -> notifications
        self.notification_preferences: Dict[str, Dict[str, bool]] = {}  # user_id -> preferences
    
    def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        content: str,
        data: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> str:
        """Send notification to user"""
        
        # Check if user wants this type of notification
        if not self._should_send_notification(user_id, notification_type):
            logger.debug(f"Skipping notification for {user_id} - disabled in preferences")
            return ""
        
        notification_id = str(uuid.uuid4())
        
        notification = Notification(
            notification_id=notification_id,
            user_id=user_id,
            type=notification_type,
            title=title,
            content=content,
            data=data or {},
            priority=priority
        )
        
        if user_id not in self.notifications:
            self.notifications[user_id] = []
        
        self.notifications[user_id].append(notification)
        
        # Keep only last 100 notifications per user
        if len(self.notifications[user_id]) > 100:
            self.notifications[user_id] = self.notifications[user_id][-100:]
        
        logger.info(f"Sent {notification_type.value} notification to {user_id}")
        return notification_id
    
    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user"""
        
        user_notifications = self.notifications.get(user_id, [])
        
        if unread_only:
            user_notifications = [n for n in user_notifications if not n.is_read]
        
        # Sort by creation time (newest first) and limit
        sorted_notifications = sorted(
            user_notifications,
            key=lambda x: x.created_at,
            reverse=True
        )
        
        return sorted_notifications[:limit]
    
    def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Mark a notification as read"""
        
        user_notifications = self.notifications.get(user_id, [])
        
        for notification in user_notifications:
            if notification.notification_id == notification_id:
                notification.mark_read()
                logger.debug(f"Marked notification {notification_id} as read for {user_id}")
                return True
        
        logger.warning(f"Notification {notification_id} not found for user {user_id}")
        return False
    
    def mark_all_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        
        user_notifications = self.notifications.get(user_id, [])
        count = 0
        
        for notification in user_notifications:
            if not notification.is_read:
                notification.mark_read()
                count += 1
        
        logger.info(f"Marked {count} notifications as read for {user_id}")
        return count
    
    def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """Delete a notification"""
        
        if user_id not in self.notifications:
            return False
        
        user_notifications = self.notifications[user_id]
        original_count = len(user_notifications)
        
        self.notifications[user_id] = [
            n for n in user_notifications
            if n.notification_id != notification_id
        ]
        
        deleted = len(self.notifications[user_id]) < original_count
        
        if deleted:
            logger.debug(f"Deleted notification {notification_id} for {user_id}")
        
        return deleted
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        
        user_notifications = self.notifications.get(user_id, [])
        return len([n for n in user_notifications if not n.is_read])
    
    def get_notification_summary(self, user_id: str) -> Dict[str, Any]:
        """Get notification summary for a user"""
        
        user_notifications = self.notifications.get(user_id, [])
        unread = [n for n in user_notifications if not n.is_read]
        
        # Count by type
        type_counts = {}
        for notification in unread:
            nt = notification.type.value
            if nt not in type_counts:
                type_counts[nt] = 0
            type_counts[nt] += 1
        
        # Count by priority
        priority_counts = {}
        for notification in unread:
            priority = notification.priority
            if priority not in priority_counts:
                priority_counts[priority] = 0
            priority_counts[priority] += 1
        
        return {
            "total": len(user_notifications),
            "unread": len(unread),
            "unread_by_type": type_counts,
            "unread_by_priority": priority_counts,
            "recent": [n.to_dict() for n in user_notifications[:5]]
        }
    
    def set_notification_preferences(
        self,
        user_id: str,
        preferences: Dict[str, bool]
    ):
        """Set notification preferences for a user"""
        
        self.notification_preferences[user_id] = preferences
        logger.info(f"Updated notification preferences for {user_id}")
    
    def get_notification_preferences(self, user_id: str) -> Dict[str, bool]:
        """Get notification preferences for a user"""
        
        return self.notification_preferences.get(user_id, self._get_default_preferences())
    
    def notify_schema_change_proposed(
        self,
        reviewers: List[str],
        change_id: str,
        schema_name: str,
        proposed_by: str
    ):
        """Send notifications for new schema change proposal"""
        
        for reviewer_id in reviewers:
            self.send_notification(
                user_id=reviewer_id,
                notification_type=NotificationType.SCHEMA_CHANGE_PROPOSED,
                title=f"New schema change proposed",
                content=f"{proposed_by} proposed changes to '{schema_name}' schema. Review required.",
                data={
                    "change_id": change_id,
                    "schema_name": schema_name,
                    "proposed_by": proposed_by
                },
                priority="high"
            )
    
    def notify_approval_requested(
        self,
        reviewer_id: str,
        change_id: str,
        schema_name: str,
        proposed_by: str
    ):
        """Send notification for approval request"""
        
        self.send_notification(
            user_id=reviewer_id,
            notification_type=NotificationType.APPROVAL_REQUESTED,
            title=f"Approval requested",
            content=f"Your approval is requested for changes to '{schema_name}' schema.",
            data={
                "change_id": change_id,
                "schema_name": schema_name,
                "proposed_by": proposed_by
            },
            priority="high"
        )
    
    def notify_change_approved(
        self,
        proposed_by: str,
        change_id: str,
        schema_name: str,
        approved_by: str
    ):
        """Send notification when change is approved"""
        
        self.send_notification(
            user_id=proposed_by,
            notification_type=NotificationType.CHANGE_APPROVED,
            title=f"Schema change approved",
            content=f"Your changes to '{schema_name}' schema have been approved by {approved_by}.",
            data={
                "change_id": change_id,
                "schema_name": schema_name,
                "approved_by": approved_by
            },
            priority="normal"
        )
    
    def notify_change_rejected(
        self,
        proposed_by: str,
        change_id: str,
        schema_name: str,
        rejected_by: str,
        reason: str = ""
    ):
        """Send notification when change is rejected"""
        
        content = f"Your changes to '{schema_name}' schema have been rejected by {rejected_by}."
        if reason:
            content += f" Reason: {reason}"
        
        self.send_notification(
            user_id=proposed_by,
            notification_type=NotificationType.CHANGE_REJECTED,
            title=f"Schema change rejected",
            content=content,
            data={
                "change_id": change_id,
                "schema_name": schema_name,
                "rejected_by": rejected_by,
                "reason": reason
            },
            priority="normal"
        )
    
    def notify_comment_added(
        self,
        user_ids: List[str],
        change_id: str,
        schema_name: str,
        comment_by: str
    ):
        """Send notification when comment is added"""
        
        for user_id in user_ids:
            if user_id != comment_by:  # Don't notify the commenter
                self.send_notification(
                    user_id=user_id,
                    notification_type=NotificationType.COMMENT_ADDED,
                    title=f"New comment on schema change",
                    content=f"{comment_by} added a comment to changes for '{schema_name}' schema.",
                    data={
                        "change_id": change_id,
                        "schema_name": schema_name,
                        "comment_by": comment_by
                    },
                    priority="low"
                )
    
    def notify_team_invitation(
        self,
        user_id: str,
        team_name: str,
        invited_by: str,
        team_id: str
    ):
        """Send notification for team invitation"""
        
        self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TEAM_INVITATION,
            title=f"Team invitation",
            content=f"You have been invited to join the '{team_name}' team by {invited_by}.",
            data={
                "team_id": team_id,
                "team_name": team_name,
                "invited_by": invited_by
            },
            priority="normal"
        )
    
    def _should_send_notification(
        self,
        user_id: str,
        notification_type: NotificationType
    ) -> bool:
        """Check if user wants to receive this type of notification"""
        
        preferences = self.get_notification_preferences(user_id)
        return preferences.get(notification_type.value, True)
    
    def _get_default_preferences(self) -> Dict[str, bool]:
        """Get default notification preferences"""
        
        return {
            NotificationType.SCHEMA_CHANGE_PROPOSED.value: True,
            NotificationType.APPROVAL_REQUESTED.value: True,
            NotificationType.CHANGE_APPROVED.value: True,
            NotificationType.CHANGE_REJECTED.value: True,
            NotificationType.COMMENT_ADDED.value: True,
            NotificationType.TEAM_INVITATION.value: True
        }
    
    def cleanup_old_notifications(self, days: int = 30):
        """Clean up notifications older than specified days"""
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cleaned_count = 0
        
        for user_id in self.notifications:
            original_count = len(self.notifications[user_id])
            
            self.notifications[user_id] = [
                n for n in self.notifications[user_id]
                if n.created_at.timestamp() > cutoff_date
            ]
            
            cleaned_count += original_count - len(self.notifications[user_id])
        
        logger.info(f"Cleaned up {cleaned_count} old notifications")
        return cleaned_count
