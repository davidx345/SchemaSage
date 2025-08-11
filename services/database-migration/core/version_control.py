"""
Version Control Integration Service
"""
import asyncio
import aiohttp
import git
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import hashlib
import difflib

from ..models.version_control import (
    GitRepository, SchemaBranch, SchemaCommit, MergeConflict, 
    PullRequest, ChangeHistory, ConflictType, MergeStrategy
)
from ..models import SchemaInfo, MigrationPlan

class GitHubIntegration:
    """GitHub integration for schema version control."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def create_repository_webhook(self, repo: GitRepository, webhook_url: str) -> Dict[str, Any]:
        """Create webhook for repository events."""
        async with aiohttp.ClientSession() as session:
            webhook_config = {
                "name": "web",
                "active": True,
                "events": [
                    "push",
                    "pull_request",
                    "pull_request_review",
                    "create",
                    "delete"
                ],
                "config": {
                    "url": webhook_url,
                    "content_type": "json",
                    "secret": repo.webhook_secret
                }
            }
            
            url = f"{self.base_url}/repos/{repo.owner}/{repo.repository_name}/hooks"
            async with session.post(url, headers=self.headers, json=webhook_config) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create webhook: {await response.text()}")
    
    async def get_repository_info(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Get repository information."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/repos/{owner}/{repo_name}"
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Repository not found: {owner}/{repo_name}")
    
    async def create_pull_request(self, repo: GitRepository, title: str, body: str, head_branch: str, base_branch: str) -> Dict[str, Any]:
        """Create a pull request."""
        async with aiohttp.ClientSession() as session:
            pr_data = {
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch,
                "maintainer_can_modify": True
            }
            
            url = f"{self.base_url}/repos/{repo.owner}/{repo.repository_name}/pulls"
            async with session.post(url, headers=self.headers, json=pr_data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create PR: {await response.text()}")
    
    async def get_pull_request(self, repo: GitRepository, pr_number: int) -> Dict[str, Any]:
        """Get pull request information."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/repos/{repo.owner}/{repo.repository_name}/pulls/{pr_number}"
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Pull request not found: {pr_number}")
    
    async def merge_pull_request(self, repo: GitRepository, pr_number: int, commit_title: str, commit_message: str, merge_method: str = "merge") -> Dict[str, Any]:
        """Merge a pull request."""
        async with aiohttp.ClientSession() as session:
            merge_data = {
                "commit_title": commit_title,
                "commit_message": commit_message,
                "merge_method": merge_method  # merge, squash, rebase
            }
            
            url = f"{self.base_url}/repos/{repo.owner}/{repo.repository_name}/pulls/{pr_number}/merge"
            async with session.put(url, headers=self.headers, json=merge_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to merge PR: {await response.text()}")

class SchemaVersionControl:
    """Schema-specific version control operations."""
    
    def __init__(self):
        self.schema_file_patterns = [
            "*.sql",
            "migrations/*.sql", 
            "schema/*.json",
            "database/*.yml"
        ]
    
    async def initialize_schema_repository(self, repo_path: str, initial_schema: SchemaInfo) -> bool:
        """Initialize a new schema repository."""
        try:
            # Initialize git repository
            repo = git.Repo.init(repo_path)
            
            # Create initial schema files
            schema_file = f"{repo_path}/schema/initial_schema.json"
            await self._save_schema_to_file(schema_file, initial_schema)
            
            # Create initial commit
            repo.index.add([schema_file])
            repo.index.commit("Initial schema commit")
            
            return True
        except Exception as e:
            print(f"Failed to initialize schema repository: {e}")
            return False
    
    async def create_schema_branch(self, repo_path: str, branch_name: str, base_branch: str = "main") -> SchemaBranch:
        """Create a new schema branch."""
        repo = git.Repo(repo_path)
        
        # Create new branch from base
        base_commit = repo.heads[base_branch].commit
        new_branch = repo.create_head(branch_name, base_commit)
        new_branch.checkout()
        
        # Create schema branch object
        schema_branch = SchemaBranch(
            branch_name=branch_name,
            base_branch=base_branch,
            last_commit_sha=str(base_commit.hexsha),
            created_by="system",  # Would be actual user in real implementation
            workspace_id="default",  # Would be actual workspace
            repo_id="default"  # Would be actual repo ID
        )
        
        return schema_branch
    
    async def commit_schema_changes(self, repo_path: str, schema: SchemaInfo, migration_plan: MigrationPlan, commit_message: str) -> SchemaCommit:
        """Commit schema changes to repository."""
        repo = git.Repo(repo_path)
        
        # Save updated schema
        schema_file = f"{repo_path}/schema/current_schema.json"
        await self._save_schema_to_file(schema_file, schema)
        
        # Save migration plan
        migration_file = f"{repo_path}/migrations/{migration_plan.plan_id}.json"
        await self._save_migration_plan_to_file(migration_file, migration_plan)
        
        # Stage and commit changes
        repo.index.add([schema_file, migration_file])
        commit = repo.index.commit(commit_message)
        
        # Create schema commit object
        schema_commit = SchemaCommit(
            commit_sha=str(commit.hexsha),
            parent_commit_sha=str(commit.parents[0].hexsha) if commit.parents else None,
            author_id="system",  # Would be actual user
            message=commit_message,
            migration_plan_id=migration_plan.plan_id,
            files_changed=[schema_file, migration_file],
            workspace_id="default",  # Would be actual workspace
            branch_id="default"  # Would be actual branch ID
        )
        
        return schema_commit
    
    async def detect_merge_conflicts(self, repo_path: str, source_branch: str, target_branch: str) -> List[MergeConflict]:
        """Detect schema merge conflicts between branches."""
        repo = git.Repo(repo_path)
        conflicts = []
        
        try:
            # Get schemas from both branches
            source_schema = await self._get_schema_from_branch(repo, source_branch)
            target_schema = await self._get_schema_from_branch(repo, target_branch)
            
            # Compare schemas and find conflicts
            conflicts.extend(await self._compare_schemas_for_conflicts(source_schema, target_schema))
            
        except Exception as e:
            print(f"Error detecting conflicts: {e}")
        
        return conflicts
    
    async def resolve_merge_conflict(self, conflict: MergeConflict, resolution: Dict[str, Any], strategy: MergeStrategy) -> MergeConflict:
        """Resolve a schema merge conflict."""
        conflict.resolution = resolution
        conflict.merge_strategy = strategy
        conflict.status = "resolved"
        conflict.resolved_at = datetime.utcnow()
        
        return conflict
    
    async def _save_schema_to_file(self, file_path: str, schema: SchemaInfo):
        """Save schema information to file."""
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(schema.model_dump(), f, indent=2, default=str)
    
    async def _save_migration_plan_to_file(self, file_path: str, migration_plan: MigrationPlan):
        """Save migration plan to file."""
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(migration_plan.model_dump(), f, indent=2, default=str)
    
    async def _get_schema_from_branch(self, repo: git.Repo, branch_name: str) -> Optional[SchemaInfo]:
        """Get schema from specific branch."""
        try:
            branch = repo.heads[branch_name]
            schema_file_path = "schema/current_schema.json"
            
            # Get file content from branch
            blob = branch.commit.tree / schema_file_path
            schema_data = json.loads(blob.data_stream.read().decode())
            
            return SchemaInfo(**schema_data)
        except Exception:
            return None
    
    async def _compare_schemas_for_conflicts(self, source_schema: SchemaInfo, target_schema: SchemaInfo) -> List[MergeConflict]:
        """Compare schemas and identify conflicts."""
        conflicts = []
        
        if not source_schema or not target_schema:
            return conflicts
        
        # Compare tables
        source_tables = {table.name: table for table in source_schema.tables}
        target_tables = {table.name: table for table in target_schema.tables}
        
        for table_name in set(source_tables.keys()) & set(target_tables.keys()):
            source_table = source_tables[table_name]
            target_table = target_tables[table_name]
            
            # Compare columns
            source_columns = {col.name: col for col in source_table.columns}
            target_columns = {col.name: col for col in target_table.columns}
            
            for col_name in set(source_columns.keys()) & set(target_columns.keys()):
                source_col = source_columns[col_name]
                target_col = target_columns[col_name]
                
                if source_col.data_type != target_col.data_type:
                    conflict = MergeConflict(
                        workspace_id="default",
                        source_branch_id="source",
                        target_branch_id="target",
                        conflict_type=ConflictType.DATA_TYPE_CONFLICT,
                        object_name=f"{table_name}.{col_name}",
                        object_type="column",
                        source_state=source_col.model_dump(),
                        target_state=target_col.model_dump()
                    )
                    conflicts.append(conflict)
        
        return conflicts

class ChangeHistoryTracker:
    """Tracks comprehensive change history."""
    
    def __init__(self):
        self.change_types = [
            "create", "update", "delete", "rename", 
            "add_column", "drop_column", "modify_column",
            "add_index", "drop_index", "add_constraint", "drop_constraint"
        ]
    
    async def track_schema_change(self, workspace_id: str, object_type: str, object_id: str, change_type: str, before_state: Any, after_state: Any, context: Dict[str, Any] = None) -> ChangeHistory:
        """Track a schema change."""
        # Calculate diff
        diff = await self._calculate_diff(before_state, after_state)
        
        change_history = ChangeHistory(
            workspace_id=workspace_id,
            object_type=object_type,
            object_id=object_id,
            change_type=change_type,
            before_state=before_state.model_dump() if hasattr(before_state, 'model_dump') else before_state,
            after_state=after_state.model_dump() if hasattr(after_state, 'model_dump') else after_state,
            diff=diff,
            branch_id=context.get("branch_id") if context else None,
            commit_id=context.get("commit_id") if context else None,
            migration_plan_id=context.get("migration_plan_id") if context else None,
            changed_by=context.get("user_id", "system") if context else "system",
            reason=context.get("reason") if context else None,
            tags=context.get("tags", []) if context else []
        )
        
        return change_history
    
    async def get_object_history(self, workspace_id: str, object_type: str, object_id: str) -> List[ChangeHistory]:
        """Get complete history for an object."""
        # This would query the database for all changes to the object
        # For now, returning empty list as placeholder
        return []
    
    async def get_workspace_activity(self, workspace_id: str, since: datetime = None, limit: int = 100) -> List[ChangeHistory]:
        """Get recent activity in workspace."""
        # This would query the database for recent changes
        # For now, returning empty list as placeholder
        return []
    
    async def _calculate_diff(self, before: Any, after: Any) -> Dict[str, Any]:
        """Calculate diff between two objects."""
        if not before or not after:
            return {"type": "full_change"}
        
        before_str = json.dumps(before, sort_keys=True, default=str)
        after_str = json.dumps(after, sort_keys=True, default=str)
        
        if before_str == after_str:
            return {"type": "no_change"}
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            before_str.splitlines(keepends=True),
            after_str.splitlines(keepends=True),
            fromfile="before",
            tofile="after"
        ))
        
        return {
            "type": "diff",
            "unified_diff": "".join(diff_lines),
            "changes_count": len([line for line in diff_lines if line.startswith(('+', '-')) and not line.startswith(('+++', '---'))])
        }

class BranchManagement:
    """Branch-based schema management."""
    
    def __init__(self, version_control: SchemaVersionControl):
        self.version_control = version_control
    
    async def create_feature_branch(self, workspace_id: str, repo_id: str, branch_name: str, base_branch: str = "main") -> SchemaBranch:
        """Create a new feature branch for schema changes."""
        # This would integrate with the actual git repository
        schema_branch = SchemaBranch(
            workspace_id=workspace_id,
            repo_id=repo_id,
            branch_name=branch_name,
            base_branch=base_branch,
            created_by="system"  # Would be actual user
        )
        
        return schema_branch
    
    async def merge_branch(self, workspace_id: str, source_branch_id: str, target_branch_id: str, merge_strategy: MergeStrategy = MergeStrategy.AUTO_MERGE) -> bool:
        """Merge schema branch."""
        # Check for conflicts
        conflicts = await self.version_control.detect_merge_conflicts("", "source", "target")
        
        if conflicts and merge_strategy == MergeStrategy.AUTO_MERGE:
            return False  # Cannot auto-merge with conflicts
        
        # Perform merge based on strategy
        if merge_strategy == MergeStrategy.AUTO_MERGE:
            return await self._auto_merge(source_branch_id, target_branch_id)
        elif merge_strategy == MergeStrategy.MANUAL_REVIEW:
            return await self._create_merge_request(source_branch_id, target_branch_id)
        
        return False
    
    async def _auto_merge(self, source_branch_id: str, target_branch_id: str) -> bool:
        """Perform automatic merge."""
        # Implementation would handle the actual git merge
        return True
    
    async def _create_merge_request(self, source_branch_id: str, target_branch_id: str) -> bool:
        """Create merge request for manual review."""
        # Implementation would create a pull request
        return True
