"""
Team Collaboration & Schema Registry Module

This module provides enterprise schema governance with collaboration features
including team management, schema versioning, change approval workflows,
and notification systems.
"""

from .models import (
    ApprovalStatus,
    ChangeType,
    UserRole,
    NotificationType,
    TeamMember,
    Team,
    Comment,
    SchemaChange,
    SchemaVersion,
    SchemaRegistry,
    Notification,
    ApprovalWorkflow
)

from .team_manager import TeamManager
from .schema_registry import SchemaRegistryManager
from .change_manager import ChangeManager
from .notification_manager import NotificationManager

__all__ = [
    'ApprovalStatus',
    'ChangeType',
    'UserRole',
    'NotificationType',
    'TeamMember',
    'Team',
    'Comment',
    'SchemaChange',
    'SchemaVersion',
    'SchemaRegistry',
    'Notification',
    'ApprovalWorkflow',
    'TeamManager',
    'SchemaRegistryManager',
    'ChangeManager',
    'NotificationManager',
    'TeamCollaborationManager'
]


class TeamCollaborationManager:
    """
    Main manager class that orchestrates team collaboration, schema governance,
    and change management workflows.
    """
    
    def __init__(self):
        self.team_manager = TeamManager()
        self.schema_registry = SchemaRegistryManager()
        self.change_manager = ChangeManager()
        self.notification_manager = NotificationManager()
    
    # Team Management Methods
    
    def create_team(self, name: str, description: str, created_by: str, settings: dict = None) -> str:
        """Create a new team workspace"""
        return self.team_manager.create_team(name, description, created_by, settings)
    
    def add_team_member(self, team_id: str, user_id: str, role: UserRole, invited_by: str) -> bool:
        """Add a member to a team"""
        success = self.team_manager.add_team_member(team_id, user_id, role, invited_by)
        
        if success:
            # Send notification
            team = self.team_manager.get_team(team_id)
            if team:
                self.notification_manager.notify_team_invitation(
                    user_id, team.name, invited_by, team_id
                )
        
        return success
    
    def update_member_role(self, team_id: str, user_id: str, new_role: UserRole, updated_by: str) -> bool:
        """Update a team member's role"""
        return self.team_manager.update_member_role(team_id, user_id, new_role, updated_by)
    
    def get_team(self, team_id: str) -> Team:
        """Get team by ID"""
        return self.team_manager.get_team(team_id)
    
    def list_teams(self, user_id: str = None) -> list:
        """List teams, optionally filtered by user membership"""
        return self.team_manager.list_teams(user_id)
    
    # Schema Registry Methods
    
    def register_schema(self, name: str, description: str, team_id: str, category: str,
                       initial_definition: dict, created_by: str, tags: list = None) -> str:
        """Register a new schema in the registry"""
        return self.schema_registry.register_schema(
            name, description, team_id, category, initial_definition, created_by, tags
        )
    
    def get_schema(self, schema_id: str) -> SchemaRegistry:
        """Get schema by ID"""
        return self.schema_registry.get_schema(schema_id)
    
    def list_schemas(self, team_id: str = None, category: str = None, tags: list = None) -> list:
        """List schemas with optional filtering"""
        return self.schema_registry.list_schemas(team_id, category, tags)
    
    def create_schema_version(self, schema_id: str, version_number: str, definition: dict,
                             created_by: str, change_summary: str = "", tags: list = None) -> str:
        """Create a new version of a schema"""
        return self.schema_registry.create_schema_version(
            schema_id, version_number, definition, created_by, change_summary, tags
        )
    
    # Change Management Methods
    
    def propose_schema_change(self, schema_id: str, change_type: ChangeType, description: str,
                             proposed_definition: dict, proposed_by: str, reviewers: list = None) -> str:
        """Propose a change to an existing schema"""
        
        schema = self.schema_registry.get_schema(schema_id)
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")
        
        # Check if user has permission to propose changes
        team = self.team_manager.get_team(schema.team_id)
        if not team:
            raise ValueError(f"Team {schema.team_id} not found")
        
        member = team.get_member(proposed_by)
        if not member or not member.has_permission("propose_changes"):
            raise ValueError(f"User {proposed_by} doesn't have permission to propose changes")
        
        # Get current schema definition
        current_version = schema.get_active_version()
        if not current_version:
            raise ValueError(f"No active version found for schema {schema_id}")
        
        # Auto-assign reviewers if not specified
        if not reviewers:
            reviewers = self._get_auto_reviewers(schema.team_id, proposed_by)
        
        change_id = self.change_manager.propose_change(
            schema_id=schema_id,
            change_type=change_type,
            description=description,
            current_definition=current_version.definition,
            proposed_definition=proposed_definition,
            proposed_by=proposed_by,
            reviewers=reviewers,
            team_id=schema.team_id
        )
        
        # Notify reviewers
        self.notification_manager.notify_schema_change_proposed(
            reviewers, change_id, schema.name, proposed_by
        )
        
        return change_id
    
    def review_schema_change(self, change_id: str, reviewer_id: str, approved: bool, comment: str = "") -> bool:
        """Review and approve/reject a schema change"""
        
        change = self.change_manager.get_change(change_id)
        if not change:
            return False
        
        # Check if user is authorized to review
        if reviewer_id not in change.reviewers:
            return False
        
        success = self.change_manager.review_change(change_id, reviewer_id, approved, comment)
        
        if success:
            # Send notifications
            schema = self.schema_registry.get_schema(change.schema_id)
            schema_name = schema.name if schema else "Unknown"
            
            if approved:
                self.notification_manager.notify_change_approved(
                    change.proposed_by, change_id, schema_name, reviewer_id
                )
            else:
                self.notification_manager.notify_change_rejected(
                    change.proposed_by, change_id, schema_name, reviewer_id, comment
                )
        
        return success
    
    def add_comment(self, change_id: str, user_id: str, content: str, parent_comment_id: str = None) -> str:
        """Add comment to a change"""
        
        comment_id = self.change_manager.add_comment(change_id, user_id, content, parent_comment_id)
        
        if comment_id:
            # Notify interested parties
            change = self.change_manager.get_change(change_id)
            if change:
                schema = self.schema_registry.get_schema(change.schema_id)
                schema_name = schema.name if schema else "Unknown"
                
                # Notify proposer and reviewers
                notify_users = [change.proposed_by] + change.reviewers
                self.notification_manager.notify_comment_added(
                    notify_users, change_id, schema_name, user_id
                )
        
        return comment_id
    
    def get_pending_changes(self, user_id: str) -> list:
        """Get pending changes for a user"""
        return self.change_manager.list_pending_changes(user_id=user_id)
    
    # Notification Methods
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> list:
        """Get notifications for a user"""
        return self.notification_manager.get_user_notifications(user_id, unread_only)
    
    def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read"""
        return self.notification_manager.mark_notification_read(user_id, notification_id)
    
    def get_notification_summary(self, user_id: str) -> dict:
        """Get notification summary for a user"""
        return self.notification_manager.get_notification_summary(user_id)
    
    # Search Methods
    
    def search_schemas(self, query: str, team_id: str = None, tags: list = None) -> list:
        """Search schemas by name, description, or tags"""
        schemas = self.schema_registry.search_schemas(query, team_id)
        
        if tags:
            schemas = [s for s in schemas if any(tag in s.tags for tag in tags)]
        
        return schemas
    
    def search_teams(self, query: str, user_id: str = None) -> list:
        """Search teams by name or description"""
        return self.team_manager.search_teams(query, user_id)
    
    # Utility Methods
    
    def _get_auto_reviewers(self, team_id: str, proposed_by: str) -> list:
        """Get automatic reviewers for a change"""
        
        team = self.team_manager.get_team(team_id)
        if not team:
            return []
        
        # Get members with review permissions (excluding proposer)
        reviewers = []
        for member in team.members:
            if (member.user_id != proposed_by and 
                member.has_permission("review_changes")):
                reviewers.append(member.user_id)
        
        return reviewers
    
    def get_dashboard_data(self, user_id: str) -> dict:
        """Get dashboard data for a user"""
        
        # Get user teams
        teams = self.team_manager.get_user_teams(user_id)
        
        # Get pending changes for user
        pending_changes = self.change_manager.list_pending_changes(user_id=user_id)
        
        # Get recent notifications
        notifications = self.notification_manager.get_user_notifications(user_id, limit=5)
        
        # Get notification summary
        notification_summary = self.notification_manager.get_notification_summary(user_id)
        
        return {
            "user_id": user_id,
            "teams": [team.to_dict() for team in teams],
            "pending_changes": [change.to_dict() for change in pending_changes],
            "recent_notifications": [n.to_dict() for n in notifications],
            "notification_summary": notification_summary,
            "stats": {
                "team_count": len(teams),
                "pending_change_count": len(pending_changes),
                "unread_notification_count": notification_summary.get("unread", 0)
            }
        }


# Global collaboration manager instance
_collaboration_manager = None

def get_collaboration_manager() -> TeamCollaborationManager:
    """Get the global collaboration manager instance"""
    global _collaboration_manager
    if _collaboration_manager is None:
        _collaboration_manager = TeamCollaborationManager()
    return _collaboration_manager
