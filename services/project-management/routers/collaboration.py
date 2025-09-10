"""
Team Collaboration API Routes

Handles team management, collaboration features, and shared workspace functionality.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Router for team collaboration
router = APIRouter(prefix="/teams", tags=["collaboration"])


@router.post("/")
async def create_team(team_data: Dict[str, Any]):
    """Create a new team"""
    try:
        team = {
            "id": 5001,
            "name": team_data.get("name", ""),
            "description": team_data.get("description", ""),
            "created_by": team_data.get("created_by", 1),
            "settings": {
                "visibility": team_data.get("visibility", "private"),  # public, private, invite_only
                "permissions": {
                    "can_edit_schemas": team_data.get("can_edit_schemas", True),
                    "can_create_projects": team_data.get("can_create_projects", True),
                    "can_invite_members": team_data.get("can_invite_members", False),
                    "can_manage_settings": team_data.get("can_manage_settings", False)
                },
                "notification_preferences": {
                    "schema_changes": True,
                    "new_comments": True,
                    "project_updates": True
                }
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "member_count": 1,
            "project_count": 0,
            "schema_count": 0
        }
        
        return {
            "team": team,
            "message": "Team created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating team: {e}")
        raise HTTPException(status_code=500, detail="Failed to create team")


@router.get("/{team_id}")
async def get_team(team_id: int):
    """Get team details"""
    try:
        team = {
            "id": team_id,
            "name": "Data Engineering Team",
            "description": "Team responsible for database schema design and data pipeline management",
            "created_by": 1,
            "settings": {
                "visibility": "private",
                "permissions": {
                    "can_edit_schemas": True,
                    "can_create_projects": True,
                    "can_invite_members": True,
                    "can_manage_settings": True
                },
                "notification_preferences": {
                    "schema_changes": True,
                    "new_comments": True,
                    "project_updates": True
                }
            },
            "created_at": "2024-01-10T09:00:00Z",
            "updated_at": "2024-01-15T14:30:00Z",
            "member_count": 5,
            "project_count": 3,
            "schema_count": 12,
            "recent_activity": [
                {
                    "type": "schema_updated",
                    "user": "john_doe",
                    "schema": "user_management",
                    "timestamp": "2024-01-15T14:30:00Z"
                },
                {
                    "type": "member_joined",
                    "user": "alice_cooper",
                    "timestamp": "2024-01-15T10:15:00Z"
                }
            ]
        }
        
        return team
        
    except Exception as e:
        logger.error(f"Error getting team: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve team")


@router.get("/{team_id}/members")
async def get_team_members(
    team_id: int,
    role: Optional[str] = None,
    status: Optional[str] = None
):
    """Get team members"""
    try:
        mock_members = [
            {
                "user_id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "role": "owner",
                "status": "active",
                "joined_at": "2024-01-10T09:00:00Z",
                "permissions": {
                    "can_edit_schemas": True,
                    "can_create_projects": True,
                    "can_invite_members": True,
                    "can_manage_settings": True
                },
                "activity": {
                    "last_active": "2024-01-15T14:30:00Z",
                    "schemas_contributed": 8,
                    "comments_made": 24
                }
            },
            {
                "user_id": 2,
                "username": "jane_smith",
                "email": "jane@example.com",
                "role": "admin",
                "status": "active",
                "joined_at": "2024-01-11T10:30:00Z",
                "permissions": {
                    "can_edit_schemas": True,
                    "can_create_projects": True,
                    "can_invite_members": True,
                    "can_manage_settings": False
                },
                "activity": {
                    "last_active": "2024-01-15T12:00:00Z",
                    "schemas_contributed": 5,
                    "comments_made": 18
                }
            },
            {
                "user_id": 3,
                "username": "mike_wilson",
                "email": "mike@example.com",
                "role": "member",
                "status": "active",
                "joined_at": "2024-01-12T14:00:00Z",
                "permissions": {
                    "can_edit_schemas": True,
                    "can_create_projects": False,
                    "can_invite_members": False,
                    "can_manage_settings": False
                },
                "activity": {
                    "last_active": "2024-01-15T09:45:00Z",
                    "schemas_contributed": 3,
                    "comments_made": 12
                }
            },
            {
                "user_id": 4,
                "username": "alice_cooper",
                "email": "alice@example.com",
                "role": "member",
                "status": "pending",
                "joined_at": "2024-01-15T10:15:00Z",
                "permissions": {
                    "can_edit_schemas": False,
                    "can_create_projects": False,
                    "can_invite_members": False,
                    "can_manage_settings": False
                },
                "activity": {
                    "last_active": None,
                    "schemas_contributed": 0,
                    "comments_made": 0
                }
            }
        ]
        
        # Apply filters
        if role:
            mock_members = [m for m in mock_members if m["role"] == role]
        if status:
            mock_members = [m for m in mock_members if m["status"] == status]
        
        return {
            "members": mock_members,
            "summary": {
                "total_members": len(mock_members),
                "by_role": {
                    "owner": len([m for m in mock_members if m["role"] == "owner"]),
                    "admin": len([m for m in mock_members if m["role"] == "admin"]),
                    "member": len([m for m in mock_members if m["role"] == "member"])
                },
                "by_status": {
                    "active": len([m for m in mock_members if m["status"] == "active"]),
                    "pending": len([m for m in mock_members if m["status"] == "pending"]),
                    "inactive": len([m for m in mock_members if m["status"] == "inactive"])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting team members: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve team members")


@router.post("/{team_id}/invite")
async def invite_team_member(
    team_id: int,
    invite_data: Dict[str, Any]
):
    """Invite a user to join the team"""
    try:
        invitation = {
            "id": 6001,
            "team_id": team_id,
            "invited_by": invite_data.get("invited_by", 1),
            "invited_user": {
                "email": invite_data.get("email", ""),
                "username": invite_data.get("username")
            },
            "role": invite_data.get("role", "member"),
            "message": invite_data.get("message", ""),
            "permissions": {
                "can_edit_schemas": invite_data.get("can_edit_schemas", True),
                "can_create_projects": invite_data.get("can_create_projects", False),
                "can_invite_members": invite_data.get("can_invite_members", False),
                "can_manage_settings": invite_data.get("can_manage_settings", False)
            },
            "status": "pending",
            "expires_at": "2024-01-22T09:00:00Z",
            "created_at": datetime.now().isoformat(),
            "invitation_token": "inv_abc123def456"
        }
        
        return {
            "invitation": invitation,
            "message": "Invitation sent successfully"
        }
        
    except Exception as e:
        logger.error(f"Error inviting team member: {e}")
        raise HTTPException(status_code=500, detail="Failed to send invitation")


@router.post("/{team_id}/members/{user_id}/role")
async def update_member_role(
    team_id: int,
    user_id: int,
    role_data: Dict[str, Any]
):
    """Update a team member's role and permissions"""
    try:
        updated_member = {
            "user_id": user_id,
            "team_id": team_id,
            "role": role_data.get("role", "member"),
            "permissions": role_data.get("permissions", {}),
            "updated_by": role_data.get("updated_by", 1),
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "member": updated_member,
            "message": "Member role updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating member role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update member role")


@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: int,
    user_id: int,
    removed_by: int
):
    """Remove a member from the team"""
    try:
        return {
            "message": "Member removed successfully",
            "removed_user_id": user_id,
            "removed_by": removed_by,
            "removed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error removing team member: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove team member")


@router.get("/{team_id}/projects")
async def get_team_projects(
    team_id: int,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Get projects associated with the team"""
    try:
        mock_projects = [
            {
                "id": 101,
                "name": "E-commerce Database",
                "description": "Main database schema for the e-commerce platform",
                "status": "active",
                "created_by": 1,
                "schema_count": 5,
                "last_updated": "2024-01-15T14:30:00Z",
                "contributors": ["john_doe", "jane_smith", "mike_wilson"]
            },
            {
                "id": 102,
                "name": "User Analytics",
                "description": "Schema for user behavior tracking and analytics",
                "status": "in_development",
                "created_by": 2,
                "schema_count": 3,
                "last_updated": "2024-01-15T10:15:00Z",
                "contributors": ["jane_smith", "alice_cooper"]
            },
            {
                "id": 103,
                "name": "Inventory Management",
                "description": "Database design for inventory and warehouse management",
                "status": "completed",
                "created_by": 1,
                "schema_count": 7,
                "last_updated": "2024-01-14T16:45:00Z",
                "contributors": ["john_doe", "mike_wilson"]
            }
        ]
        
        # Apply status filter
        if status:
            mock_projects = [p for p in mock_projects if p["status"] == status]
        
        # Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_projects = mock_projects[start_idx:end_idx]
        
        return {
            "projects": paginated_projects,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(mock_projects),
                "pages": (len(mock_projects) + limit - 1) // limit
            },
            "summary": {
                "total_projects": len(mock_projects),
                "by_status": {
                    "active": len([p for p in mock_projects if p["status"] == "active"]),
                    "in_development": len([p for p in mock_projects if p["status"] == "in_development"]),
                    "completed": len([p for p in mock_projects if p["status"] == "completed"]),
                    "archived": len([p for p in mock_projects if p["status"] == "archived"])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting team projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve team projects")


@router.get("/{team_id}/activity")
async def get_team_activity(
    team_id: int,
    activity_type: Optional[str] = None,
    days: int = Query(7, ge=1, le=30),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get team activity feed"""
    try:
        mock_activities = [
            {
                "id": 7001,
                "type": "schema_created",
                "user": {
                    "user_id": 1,
                    "username": "john_doe"
                },
                "details": {
                    "schema_name": "payment_processing",
                    "project_id": 101,
                    "project_name": "E-commerce Database"
                },
                "timestamp": "2024-01-15T14:30:00Z"
            },
            {
                "id": 7002,
                "type": "comment_added",
                "user": {
                    "user_id": 2,
                    "username": "jane_smith"
                },
                "details": {
                    "comment_id": 1001,
                    "schema_name": "user_profiles",
                    "content": "Great work on the user table structure!"
                },
                "timestamp": "2024-01-15T12:15:00Z"
            },
            {
                "id": 7003,
                "type": "member_joined",
                "user": {
                    "user_id": 4,
                    "username": "alice_cooper"
                },
                "details": {
                    "invited_by": "john_doe",
                    "role": "member"
                },
                "timestamp": "2024-01-15T10:15:00Z"
            },
            {
                "id": 7004,
                "type": "project_created",
                "user": {
                    "user_id": 2,
                    "username": "jane_smith"
                },
                "details": {
                    "project_id": 102,
                    "project_name": "User Analytics",
                    "description": "Schema for user behavior tracking"
                },
                "timestamp": "2024-01-14T16:30:00Z"
            }
        ]
        
        # Filter by activity type
        if activity_type:
            mock_activities = [a for a in mock_activities if a["type"] == activity_type]
        
        # Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_activities = mock_activities[start_idx:end_idx]
        
        return {
            "activities": paginated_activities,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(mock_activities),
                "pages": (len(mock_activities) + limit - 1) // limit
            },
            "summary": {
                "total_activities": len(mock_activities),
                "timeframe_days": days,
                "by_type": {
                    "schema_created": len([a for a in mock_activities if a["type"] == "schema_created"]),
                    "schema_updated": len([a for a in mock_activities if a["type"] == "schema_updated"]),
                    "comment_added": len([a for a in mock_activities if a["type"] == "comment_added"]),
                    "member_joined": len([a for a in mock_activities if a["type"] == "member_joined"]),
                    "project_created": len([a for a in mock_activities if a["type"] == "project_created"])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting team activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve team activity")


@router.put("/{team_id}/settings")
async def update_team_settings(
    team_id: int,
    settings_data: Dict[str, Any]
):
    """Update team settings"""
    try:
        updated_settings = {
            "team_id": team_id,
            "visibility": settings_data.get("visibility", "private"),
            "permissions": settings_data.get("permissions", {}),
            "notification_preferences": settings_data.get("notification_preferences", {}),
            "updated_by": settings_data.get("updated_by", 1),
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "settings": updated_settings,
            "message": "Team settings updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating team settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update team settings")


@router.post("/{team_id}/share-schema")
async def share_schema_with_team(
    team_id: int,
    share_data: Dict[str, Any]
):
    """Share a schema with the team"""
    try:
        shared_schema = {
            "id": 8001,
            "schema_id": share_data.get("schema_id"),
            "team_id": team_id,
            "shared_by": share_data.get("shared_by", 1),
            "permissions": {
                "can_view": True,
                "can_edit": share_data.get("can_edit", False),
                "can_comment": share_data.get("can_comment", True),
                "can_download": share_data.get("can_download", True)
            },
            "message": share_data.get("message", ""),
            "shared_at": datetime.now().isoformat()
        }
        
        return {
            "shared_schema": shared_schema,
            "message": "Schema shared with team successfully"
        }
        
    except Exception as e:
        logger.error(f"Error sharing schema with team: {e}")
        raise HTTPException(status_code=500, detail="Failed to share schema with team")


@router.get("/user/{user_id}")
async def get_user_teams(user_id: int):
    """Get all teams for a user"""
    try:
        mock_teams = [
            {
                "id": 5001,
                "name": "Data Engineering Team",
                "role": "owner",
                "member_count": 5,
                "project_count": 3,
                "last_activity": "2024-01-15T14:30:00Z"
            },
            {
                "id": 5002,
                "name": "Frontend Development",
                "role": "member",
                "member_count": 8,
                "project_count": 2,
                "last_activity": "2024-01-15T11:45:00Z"
            },
            {
                "id": 5003,
                "name": "Product Team",
                "role": "admin",
                "member_count": 12,
                "project_count": 5,
                "last_activity": "2024-01-14T09:20:00Z"
            }
        ]
        
        return {
            "teams": mock_teams,
            "summary": {
                "total_teams": len(mock_teams),
                "roles": {
                    "owner": len([t for t in mock_teams if t["role"] == "owner"]),
                    "admin": len([t for t in mock_teams if t["role"] == "admin"]),
                    "member": len([t for t in mock_teams if t["role"] == "member"])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user teams: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user teams")
