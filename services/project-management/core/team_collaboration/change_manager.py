"""
Change management system for schema collaboration
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import (
    SchemaChange, ChangeType, ApprovalStatus, Comment, 
    Notification, NotificationType, ApprovalWorkflow, Team
)

logger = logging.getLogger(__name__)


class ChangeManager:
    """
    Manages schema change proposals, reviews, and approvals
    """
    
    def __init__(self):
        self.pending_changes: Dict[str, SchemaChange] = {}
        self.approved_changes: Dict[str, SchemaChange] = {}
        self.rejected_changes: Dict[str, SchemaChange] = {}
        self.workflows: Dict[str, ApprovalWorkflow] = {}
    
    def propose_change(
        self,
        schema_id: str,
        change_type: ChangeType,
        description: str,
        current_definition: Dict[str, Any],
        proposed_definition: Dict[str, Any],
        proposed_by: str,
        reviewers: List[str] = None,
        team_id: str = None
    ) -> str:
        """Propose a schema change"""
        
        change_id = str(uuid.uuid4())
        
        # Analyze impact
        impact_analysis = self._analyze_change_impact(
            current_definition,
            proposed_definition,
            change_type
        )
        
        # Get reviewers if not specified
        if not reviewers and team_id:
            reviewers = self._get_auto_reviewers(team_id, proposed_by)
        
        change = SchemaChange(
            change_id=change_id,
            schema_id=schema_id,
            change_type=change_type,
            description=description,
            proposed_by=proposed_by,
            current_definition=current_definition,
            proposed_definition=proposed_definition,
            impact_analysis=impact_analysis,
            reviewers=reviewers or []
        )
        
        self.pending_changes[change_id] = change
        
        logger.info(f"Proposed schema change {change_id} for schema {schema_id}")
        return change_id
    
    def review_change(
        self,
        change_id: str,
        reviewer_id: str,
        approved: bool,
        comment: str = "",
        team_id: str = None
    ) -> bool:
        """Review and approve/reject a schema change"""
        
        if change_id not in self.pending_changes:
            logger.error(f"Change {change_id} not found in pending changes")
            return False
        
        change = self.pending_changes[change_id]
        
        # Check if user is authorized to review
        if reviewer_id not in change.reviewers:
            logger.error(f"User {reviewer_id} not authorized to review change {change_id}")
            return False
        
        # Add comment if provided
        if comment:
            comment_obj = Comment(
                comment_id=str(uuid.uuid4()),
                user_id=reviewer_id,
                content=comment,
                thread_id=change_id
            )
            change.add_comment(comment_obj)
        
        # Record approval/rejection
        if approved:
            if reviewer_id not in change.approved_by:
                change.approved_by.append(reviewer_id)
            # Remove from rejected if previously rejected
            if reviewer_id in change.rejected_by:
                change.rejected_by.remove(reviewer_id)
        else:
            if reviewer_id not in change.rejected_by:
                change.rejected_by.append(reviewer_id)
            # Remove from approved if previously approved
            if reviewer_id in change.approved_by:
                change.approved_by.remove(reviewer_id)
        
        # Check if change should be approved or rejected
        workflow = self._get_workflow_for_change(change, team_id)
        required_approvals = workflow.required_approvals if workflow else 1
        
        if len(change.approved_by) >= required_approvals:
            change.status = ApprovalStatus.APPROVED
            self.approved_changes[change_id] = change
            del self.pending_changes[change_id]
            logger.info(f"Change {change_id} approved")
        elif len(change.rejected_by) > 0:
            change.status = ApprovalStatus.REJECTED
            self.rejected_changes[change_id] = change
            del self.pending_changes[change_id]
            logger.info(f"Change {change_id} rejected")
        
        return True
    
    def add_comment(
        self,
        change_id: str,
        user_id: str,
        content: str,
        parent_comment_id: str = None
    ) -> str:
        """Add comment to a change"""
        
        change = self._get_change_by_id(change_id)
        if not change:
            logger.error(f"Change {change_id} not found")
            return ""
        
        comment_id = str(uuid.uuid4())
        comment = Comment(
            comment_id=comment_id,
            user_id=user_id,
            content=content,
            thread_id=change_id,
            parent_comment_id=parent_comment_id
        )
        
        change.add_comment(comment)
        
        logger.info(f"Added comment {comment_id} to change {change_id}")
        return comment_id
    
    def get_change(self, change_id: str) -> Optional[SchemaChange]:
        """Get change by ID"""
        return self._get_change_by_id(change_id)
    
    def list_pending_changes(
        self,
        user_id: str = None,
        schema_id: str = None,
        team_id: str = None
    ) -> List[SchemaChange]:
        """List pending changes with optional filtering"""
        
        changes = list(self.pending_changes.values())
        
        if user_id:
            changes = [c for c in changes if user_id in c.reviewers or c.proposed_by == user_id]
        
        if schema_id:
            changes = [c for c in changes if c.schema_id == schema_id]
        
        # Note: team_id filtering would require schema registry integration
        
        return changes
    
    def list_user_changes(
        self,
        user_id: str,
        status: ApprovalStatus = None
    ) -> List[SchemaChange]:
        """List changes for a specific user"""
        
        all_changes = []
        all_changes.extend(self.pending_changes.values())
        all_changes.extend(self.approved_changes.values())
        all_changes.extend(self.rejected_changes.values())
        
        user_changes = [
            c for c in all_changes 
            if c.proposed_by == user_id or user_id in c.reviewers
        ]
        
        if status:
            user_changes = [c for c in user_changes if c.status == status]
        
        return sorted(user_changes, key=lambda x: x.proposed_at, reverse=True)
    
    def get_change_statistics(self, team_id: str = None) -> Dict[str, Any]:
        """Get change statistics"""
        
        # Note: This would be more sophisticated with team filtering
        stats = {
            "pending": len(self.pending_changes),
            "approved": len(self.approved_changes),
            "rejected": len(self.rejected_changes),
            "total": len(self.pending_changes) + len(self.approved_changes) + len(self.rejected_changes)
        }
        
        # Change type breakdown
        all_changes = []
        all_changes.extend(self.pending_changes.values())
        all_changes.extend(self.approved_changes.values())
        all_changes.extend(self.rejected_changes.values())
        
        change_types = {}
        for change in all_changes:
            ct = change.change_type.value
            if ct not in change_types:
                change_types[ct] = 0
            change_types[ct] += 1
        
        stats["change_types"] = change_types
        
        return stats
    
    def create_workflow(
        self,
        name: str,
        description: str,
        team_id: str,
        required_approvals: int = 1,
        reviewer_roles: List[str] = None,
        schema_categories: List[str] = None,
        created_by: str = ""
    ) -> str:
        """Create an approval workflow"""
        
        workflow_id = str(uuid.uuid4())
        
        from .models import UserRole
        roles = []
        if reviewer_roles:
            for role_str in reviewer_roles:
                try:
                    roles.append(UserRole(role_str))
                except ValueError:
                    continue
        
        workflow = ApprovalWorkflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            team_id=team_id,
            required_approvals=required_approvals,
            reviewer_roles=roles,
            schema_categories=schema_categories or [],
            created_by=created_by
        )
        
        self.workflows[workflow_id] = workflow
        
        logger.info(f"Created workflow {workflow_id} for team {team_id}")
        return workflow_id
    
    def get_workflow(self, workflow_id: str) -> Optional[ApprovalWorkflow]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, team_id: str = None) -> List[ApprovalWorkflow]:
        """List workflows, optionally filtered by team"""
        
        workflows = list(self.workflows.values())
        
        if team_id:
            workflows = [w for w in workflows if w.team_id == team_id]
        
        return workflows
    
    def _get_change_by_id(self, change_id: str) -> Optional[SchemaChange]:
        """Get change from any status bucket"""
        
        if change_id in self.pending_changes:
            return self.pending_changes[change_id]
        elif change_id in self.approved_changes:
            return self.approved_changes[change_id]
        elif change_id in self.rejected_changes:
            return self.rejected_changes[change_id]
        
        return None
    
    def _analyze_change_impact(
        self,
        current_definition: Dict[str, Any],
        proposed_definition: Dict[str, Any],
        change_type: ChangeType
    ) -> Dict[str, Any]:
        """Analyze the impact of a proposed change"""
        
        impact = {
            "breaking_change": False,
            "affects_existing_data": False,
            "migration_required": False,
            "estimated_effort": "low",
            "risks": []
        }
        
        # Simple impact analysis based on change type
        if change_type in [ChangeType.DROP_COLUMN, ChangeType.DROP_TABLE]:
            impact["breaking_change"] = True
            impact["affects_existing_data"] = True
            impact["migration_required"] = True
            impact["estimated_effort"] = "high"
            impact["risks"].append("Data loss possible")
        
        elif change_type in [ChangeType.MODIFY_COLUMN]:
            impact["affects_existing_data"] = True
            impact["migration_required"] = True
            impact["estimated_effort"] = "medium"
            impact["risks"].append("Data type conversion required")
        
        elif change_type in [ChangeType.ADD_COLUMN, ChangeType.ADD_INDEX]:
            impact["estimated_effort"] = "low"
        
        elif change_type in [ChangeType.ADD_TABLE]:
            impact["estimated_effort"] = "medium"
        
        # More sophisticated analysis would compare actual schemas
        
        return impact
    
    def _get_auto_reviewers(self, team_id: str, proposed_by: str) -> List[str]:
        """Get automatic reviewers for a change"""
        
        # This would integrate with team manager to get reviewers
        # For now, return empty list
        return []
    
    def _get_workflow_for_change(
        self,
        change: SchemaChange,
        team_id: str = None
    ) -> Optional[ApprovalWorkflow]:
        """Get applicable workflow for a change"""
        
        if not team_id:
            return None
        
        # Find workflows that apply to this team and schema category
        applicable_workflows = [
            w for w in self.workflows.values()
            if w.team_id == team_id and w.is_active
        ]
        
        # For now, return the first applicable workflow
        # In practice, you'd have more sophisticated matching logic
        return applicable_workflows[0] if applicable_workflows else None
