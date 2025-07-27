"""
Team management functionality for collaboration system
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from .models import Team, TeamMember, UserRole, Notification, NotificationType

logger = logging.getLogger(__name__)


class TeamManager:
    """
    Manages team operations including creation, member management, and permissions
    """
    
    def __init__(self):
        self.teams: Dict[str, Team] = {}
        self.user_teams: Dict[str, List[str]] = {}  # user_id -> list of team_ids
    
    def create_team(
        self,
        name: str,
        description: str,
        created_by: str,
        settings: Dict[str, Any] = None
    ) -> str:
        """Create a new team workspace"""
        
        team_id = str(uuid.uuid4())
        
        # Create team owner
        owner = TeamMember(
            user_id=created_by,
            username=created_by,
            email=f"{created_by}@company.com",
            role=UserRole.OWNER,
            permissions={
                "manage_team", "manage_schemas", "approve_changes",
                "invite_members", "remove_members", "change_permissions",
                "create_schemas", "propose_changes", "review_changes"
            }
        )
        
        team = Team(
            team_id=team_id,
            name=name,
            description=description,
            created_by=created_by,
            members=[owner],
            settings=settings or self._get_default_team_settings()
        )
        
        self.teams[team_id] = team
        
        # Update user teams mapping
        if created_by not in self.user_teams:
            self.user_teams[created_by] = []
        self.user_teams[created_by].append(team_id)
        
        logger.info(f"Created team {team_id}: {name}")
        return team_id
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """Get team by ID"""
        return self.teams.get(team_id)
    
    def list_teams(self, user_id: str = None) -> List[Team]:
        """List teams, optionally filtered by user membership"""
        if user_id:
            user_team_ids = self.user_teams.get(user_id, [])
            return [self.teams[team_id] for team_id in user_team_ids if team_id in self.teams]
        return list(self.teams.values())
    
    def add_team_member(
        self,
        team_id: str,
        user_id: str,
        role: UserRole,
        invited_by: str,
        username: str = None,
        email: str = None
    ) -> bool:
        """Add a member to a team"""
        
        if team_id not in self.teams:
            logger.error(f"Team {team_id} not found")
            return False
        
        team = self.teams[team_id]
        
        # Check if inviter has permission
        inviter = team.get_member(invited_by)
        if not inviter or not inviter.has_permission("invite_members"):
            logger.error(f"User {invited_by} doesn't have permission to invite members")
            return False
        
        # Check if user is already a member
        if team.has_member(user_id):
            logger.warning(f"User {user_id} is already a member of team {team_id}")
            return False
        
        member = TeamMember(
            user_id=user_id,
            username=username or user_id,
            email=email or f"{user_id}@company.com",
            role=role,
            permissions=self._get_role_permissions(role)
        )
        
        team.members.append(member)
        
        # Update user teams mapping
        if user_id not in self.user_teams:
            self.user_teams[user_id] = []
        self.user_teams[user_id].append(team_id)
        
        logger.info(f"Added user {user_id} to team {team_id} with role {role.value}")
        return True
    
    def remove_team_member(
        self,
        team_id: str,
        user_id: str,
        removed_by: str
    ) -> bool:
        """Remove a member from a team"""
        
        if team_id not in self.teams:
            logger.error(f"Team {team_id} not found")
            return False
        
        team = self.teams[team_id]
        
        # Check if remover has permission
        remover = team.get_member(removed_by)
        if not remover or not remover.has_permission("remove_members"):
            logger.error(f"User {removed_by} doesn't have permission to remove members")
            return False
        
        # Can't remove team owner
        member_to_remove = team.get_member(user_id)
        if not member_to_remove:
            logger.warning(f"User {user_id} is not a member of team {team_id}")
            return False
        
        if member_to_remove.role == UserRole.OWNER:
            logger.error("Cannot remove team owner")
            return False
        
        # Remove member
        team.members = [m for m in team.members if m.user_id != user_id]
        
        # Update user teams mapping
        if user_id in self.user_teams:
            self.user_teams[user_id] = [
                tid for tid in self.user_teams[user_id] if tid != team_id
            ]
        
        logger.info(f"Removed user {user_id} from team {team_id}")
        return True
    
    def update_member_role(
        self,
        team_id: str,
        user_id: str,
        new_role: UserRole,
        updated_by: str
    ) -> bool:
        """Update a team member's role"""
        
        if team_id not in self.teams:
            logger.error(f"Team {team_id} not found")
            return False
        
        team = self.teams[team_id]
        
        # Check permissions
        updater = team.get_member(updated_by)
        if not updater or not updater.has_permission("change_permissions"):
            logger.error(f"User {updated_by} doesn't have permission to change permissions")
            return False
        
        member = team.get_member(user_id)
        if not member:
            logger.error(f"User {user_id} is not a member of team {team_id}")
            return False
        
        # Can't change owner role
        if member.role == UserRole.OWNER:
            logger.error("Cannot change team owner role")
            return False
        
        old_role = member.role
        member.role = new_role
        member.permissions = self._get_role_permissions(new_role)
        
        logger.info(f"Updated {user_id} role from {old_role.value} to {new_role.value} in team {team_id}")
        return True
    
    def get_user_teams(self, user_id: str) -> List[Team]:
        """Get all teams a user belongs to"""
        team_ids = self.user_teams.get(user_id, [])
        return [self.teams[team_id] for team_id in team_ids if team_id in self.teams]
    
    def get_team_members(self, team_id: str, role: UserRole = None) -> List[TeamMember]:
        """Get team members, optionally filtered by role"""
        team = self.teams.get(team_id)
        if not team:
            return []
        
        if role:
            return [m for m in team.members if m.role == role]
        return team.members
    
    def user_has_permission(self, user_id: str, team_id: str, permission: str) -> bool:
        """Check if user has specific permission in team"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        member = team.get_member(user_id)
        return member and member.has_permission(permission)
    
    def update_team_settings(
        self,
        team_id: str,
        settings: Dict[str, Any],
        updated_by: str
    ) -> bool:
        """Update team settings"""
        
        if team_id not in self.teams:
            logger.error(f"Team {team_id} not found")
            return False
        
        team = self.teams[team_id]
        
        # Check permissions
        updater = team.get_member(updated_by)
        if not updater or not updater.has_permission("manage_team"):
            logger.error(f"User {updated_by} doesn't have permission to manage team")
            return False
        
        team.settings.update(settings)
        logger.info(f"Updated settings for team {team_id}")
        return True
    
    def delete_team(self, team_id: str, deleted_by: str) -> bool:
        """Delete a team"""
        
        if team_id not in self.teams:
            logger.error(f"Team {team_id} not found")
            return False
        
        team = self.teams[team_id]
        
        # Only owner can delete team
        deleter = team.get_member(deleted_by)
        if not deleter or deleter.role != UserRole.OWNER:
            logger.error(f"Only team owner can delete team")
            return False
        
        # Remove from all user team mappings
        for member in team.members:
            if member.user_id in self.user_teams:
                self.user_teams[member.user_id] = [
                    tid for tid in self.user_teams[member.user_id] if tid != team_id
                ]
        
        # Delete team
        del self.teams[team_id]
        
        logger.info(f"Deleted team {team_id}")
        return True
    
    def search_teams(
        self,
        query: str,
        user_id: str = None,
        limit: int = 50
    ) -> List[Team]:
        """Search teams by name or description"""
        
        teams_to_search = self.list_teams(user_id) if user_id else list(self.teams.values())
        
        query_lower = query.lower()
        matches = []
        
        for team in teams_to_search:
            if (query_lower in team.name.lower() or 
                query_lower in team.description.lower()):
                matches.append(team)
                
                if len(matches) >= limit:
                    break
        
        return matches
    
    def _get_default_team_settings(self) -> Dict[str, Any]:
        """Get default team settings"""
        return {
            "auto_approval_enabled": False,
            "require_review_for_breaking_changes": True,
            "notification_preferences": {
                "schema_changes": True,
                "team_updates": True,
                "approval_requests": True
            },
            "schema_naming_convention": "",
            "maximum_pending_changes": 10,
            "approval_timeout_hours": 72
        }
    
    def _get_role_permissions(self, role: UserRole) -> Set[str]:
        """Get permissions for a role"""
        base_permissions = {
            "view_schemas", "view_team"
        }
        
        role_permissions = {
            UserRole.VIEWER: set(),
            UserRole.CONTRIBUTOR: {
                "create_schemas", "propose_changes", "comment_on_changes"
            },
            UserRole.REVIEWER: {
                "create_schemas", "propose_changes", "comment_on_changes",
                "review_changes", "approve_changes"
            },
            UserRole.ADMIN: {
                "create_schemas", "propose_changes", "comment_on_changes",
                "review_changes", "approve_changes", "manage_schemas",
                "invite_members", "change_permissions"
            },
            UserRole.OWNER: {
                "create_schemas", "propose_changes", "comment_on_changes",
                "review_changes", "approve_changes", "manage_schemas",
                "invite_members", "remove_members", "change_permissions",
                "manage_team", "delete_team"
            }
        }
        
        return base_permissions | role_permissions.get(role, set())
    
    def get_team_statistics(self, team_id: str) -> Dict[str, Any]:
        """Get team statistics"""
        team = self.teams.get(team_id)
        if not team:
            return {}
        
        role_counts = {}
        for role in UserRole:
            role_counts[role.value] = len([m for m in team.members if m.role == role])
        
        return {
            "team_id": team_id,
            "name": team.name,
            "total_members": len(team.members),
            "role_breakdown": role_counts,
            "created_at": team.created_at.isoformat(),
            "settings": team.settings
        }
