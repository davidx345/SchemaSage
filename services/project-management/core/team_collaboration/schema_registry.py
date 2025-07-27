"""
Schema registry management for team collaboration
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import (
    SchemaRegistry, SchemaVersion, SchemaChange, ChangeType, 
    ApprovalStatus, Comment, Team
)

logger = logging.getLogger(__name__)


class SchemaRegistryManager:
    """
    Manages schema registry operations including versioning and change tracking
    """
    
    def __init__(self):
        self.schemas: Dict[str, SchemaRegistry] = {}
        self.team_schemas: Dict[str, List[str]] = {}  # team_id -> list of schema_ids
    
    def register_schema(
        self,
        name: str,
        description: str,
        team_id: str,
        category: str,
        initial_definition: Dict[str, Any],
        created_by: str,
        tags: List[str] = None
    ) -> str:
        """Register a new schema in the registry"""
        
        schema_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())
        
        # Create initial version
        initial_version = SchemaVersion(
            version_id=version_id,
            schema_id=schema_id,
            version_number="1.0.0",
            definition=initial_definition,
            created_by=created_by,
            change_summary="Initial schema registration",
            is_active=True,
            tags=tags or []
        )
        
        schema_registry = SchemaRegistry(
            schema_id=schema_id,
            name=name,
            description=description,
            team_id=team_id,
            category=category,
            current_version="1.0.0",
            versions=[initial_version],
            tags=tags or [],
            created_by=created_by
        )
        
        self.schemas[schema_id] = schema_registry
        
        # Update team schemas mapping
        if team_id not in self.team_schemas:
            self.team_schemas[team_id] = []
        self.team_schemas[team_id].append(schema_id)
        
        logger.info(f"Registered schema {schema_id}: {name} for team {team_id}")
        return schema_id
    
    def get_schema(self, schema_id: str) -> Optional[SchemaRegistry]:
        """Get schema by ID"""
        return self.schemas.get(schema_id)
    
    def list_schemas(
        self, 
        team_id: str = None,
        category: str = None,
        tags: List[str] = None
    ) -> List[SchemaRegistry]:
        """List schemas with optional filtering"""
        
        schemas = list(self.schemas.values())
        
        if team_id:
            schema_ids = self.team_schemas.get(team_id, [])
            schemas = [self.schemas[sid] for sid in schema_ids if sid in self.schemas]
        
        if category:
            schemas = [s for s in schemas if s.category == category]
        
        if tags:
            schemas = [s for s in schemas if any(tag in s.tags for tag in tags)]
        
        return schemas
    
    def update_schema(
        self,
        schema_id: str,
        name: str = None,
        description: str = None,
        category: str = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Update schema metadata"""
        
        schema = self.schemas.get(schema_id)
        if not schema:
            logger.error(f"Schema {schema_id} not found")
            return False
        
        if name:
            schema.name = name
        if description:
            schema.description = description
        if category:
            schema.category = category
        if tags is not None:
            schema.tags = tags
        if metadata:
            schema.metadata.update(metadata)
        
        schema.updated_at = datetime.now()
        
        logger.info(f"Updated schema {schema_id}")
        return True
    
    def create_schema_version(
        self,
        schema_id: str,
        version_number: str,
        definition: Dict[str, Any],
        created_by: str,
        change_summary: str = "",
        tags: List[str] = None
    ) -> str:
        """Create a new version of a schema"""
        
        schema = self.schemas.get(schema_id)
        if not schema:
            logger.error(f"Schema {schema_id} not found")
            return ""
        
        version_id = str(uuid.uuid4())
        
        # Get current active version for parent reference
        current_version = schema.get_active_version()
        parent_version_id = current_version.version_id if current_version else None
        
        new_version = SchemaVersion(
            version_id=version_id,
            schema_id=schema_id,
            version_number=version_number,
            definition=definition,
            created_by=created_by,
            change_summary=change_summary,
            tags=tags or [],
            parent_version_id=parent_version_id
        )
        
        schema.add_version(new_version)
        
        logger.info(f"Created version {version_number} for schema {schema_id}")
        return version_id
    
    def get_schema_version(self, schema_id: str, version_id: str) -> Optional[SchemaVersion]:
        """Get specific version of a schema"""
        
        schema = self.schemas.get(schema_id)
        if not schema:
            return None
        
        return schema.get_version(version_id)
    
    def get_schema_versions(self, schema_id: str) -> List[SchemaVersion]:
        """Get all versions of a schema"""
        
        schema = self.schemas.get(schema_id)
        if not schema:
            return []
        
        # Return sorted by creation time (newest first)
        return sorted(schema.versions, key=lambda v: v.created_at, reverse=True)
    
    def activate_version(
        self,
        schema_id: str,
        version_id: str,
        activated_by: str
    ) -> bool:
        """Activate a specific version of a schema"""
        
        schema = self.schemas.get(schema_id)
        if not schema:
            logger.error(f"Schema {schema_id} not found")
            return False
        
        version = schema.get_version(version_id)
        if not version:
            logger.error(f"Version {version_id} not found in schema {schema_id}")
            return False
        
        # Deactivate all versions
        for v in schema.versions:
            v.is_active = False
        
        # Activate target version
        version.is_active = True
        schema.current_version = version.version_number
        schema.updated_at = datetime.now()
        
        logger.info(f"Activated version {version.version_number} for schema {schema_id}")
        return True
    
    def delete_schema(self, schema_id: str) -> bool:
        """Delete a schema and all its versions"""
        
        schema = self.schemas.get(schema_id)
        if not schema:
            logger.error(f"Schema {schema_id} not found")
            return False
        
        # Remove from team mapping
        team_id = schema.team_id
        if team_id in self.team_schemas:
            self.team_schemas[team_id] = [
                sid for sid in self.team_schemas[team_id] if sid != schema_id
            ]
        
        # Delete schema
        del self.schemas[schema_id]
        
        logger.info(f"Deleted schema {schema_id}")
        return True
    
    def search_schemas(
        self,
        query: str,
        team_id: str = None,
        limit: int = 50
    ) -> List[SchemaRegistry]:
        """Search schemas by name, description, or tags"""
        
        schemas_to_search = self.list_schemas(team_id=team_id)
        
        query_lower = query.lower()
        matches = []
        
        for schema in schemas_to_search:
            if (query_lower in schema.name.lower() or 
                query_lower in schema.description.lower() or
                any(query_lower in tag.lower() for tag in schema.tags)):
                matches.append(schema)
                
                if len(matches) >= limit:
                    break
        
        return matches
    
    def get_schema_statistics(self, schema_id: str) -> Dict[str, Any]:
        """Get statistics for a schema"""
        
        schema = self.schemas.get(schema_id)
        if not schema:
            return {}
        
        versions = schema.versions
        active_version = schema.get_active_version()
        
        return {
            "schema_id": schema_id,
            "name": schema.name,
            "category": schema.category,
            "total_versions": len(versions),
            "current_version": schema.current_version,
            "created_at": schema.created_at.isoformat(),
            "updated_at": schema.updated_at.isoformat(),
            "active_version_id": active_version.version_id if active_version else None,
            "tags": schema.tags,
            "team_id": schema.team_id
        }
    
    def get_team_statistics(self, team_id: str) -> Dict[str, Any]:
        """Get schema statistics for a team"""
        
        schema_ids = self.team_schemas.get(team_id, [])
        schemas = [self.schemas[sid] for sid in schema_ids if sid in self.schemas]
        
        categories = {}
        total_versions = 0
        
        for schema in schemas:
            category = schema.category
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
            total_versions += len(schema.versions)
        
        return {
            "team_id": team_id,
            "total_schemas": len(schemas),
            "total_versions": total_versions,
            "categories": categories,
            "recent_schemas": [
                {
                    "schema_id": s.schema_id,
                    "name": s.name,
                    "updated_at": s.updated_at.isoformat()
                }
                for s in sorted(schemas, key=lambda x: x.updated_at, reverse=True)[:5]
            ]
        }
    
    def compare_versions(
        self,
        schema_id: str,
        version_a_id: str,
        version_b_id: str
    ) -> Dict[str, Any]:
        """Compare two versions of a schema"""
        
        schema = self.schemas.get(schema_id)
        if not schema:
            return {"error": f"Schema {schema_id} not found"}
        
        version_a = schema.get_version(version_a_id)
        version_b = schema.get_version(version_b_id)
        
        if not version_a:
            return {"error": f"Version {version_a_id} not found"}
        if not version_b:
            return {"error": f"Version {version_b_id} not found"}
        
        return {
            "schema_id": schema_id,
            "version_a": {
                "version_id": version_a.version_id,
                "version_number": version_a.version_number,
                "created_at": version_a.created_at.isoformat(),
                "change_summary": version_a.change_summary
            },
            "version_b": {
                "version_id": version_b.version_id,
                "version_number": version_b.version_number,
                "created_at": version_b.created_at.isoformat(),
                "change_summary": version_b.change_summary
            },
            "differences": self._compute_schema_differences(
                version_a.definition,
                version_b.definition
            )
        }
    
    def _compute_schema_differences(
        self,
        schema_a: Dict[str, Any],
        schema_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute differences between two schema definitions"""
        
        # This is a simplified diff - in production you'd want more sophisticated comparison
        differences = {
            "added": [],
            "removed": [],
            "modified": []
        }
        
        # Compare tables (simplified)
        tables_a = {t.get('name', ''): t for t in schema_a.get('tables', [])}
        tables_b = {t.get('name', ''): t for t in schema_b.get('tables', [])}
        
        # Added tables
        for table_name in set(tables_b.keys()) - set(tables_a.keys()):
            differences["added"].append({
                "type": "table",
                "name": table_name,
                "details": tables_b[table_name]
            })
        
        # Removed tables
        for table_name in set(tables_a.keys()) - set(tables_b.keys()):
            differences["removed"].append({
                "type": "table",
                "name": table_name,
                "details": tables_a[table_name]
            })
        
        # Modified tables (simplified - just check if they're different)
        for table_name in set(tables_a.keys()) & set(tables_b.keys()):
            if tables_a[table_name] != tables_b[table_name]:
                differences["modified"].append({
                    "type": "table",
                    "name": table_name,
                    "old": tables_a[table_name],
                    "new": tables_b[table_name]
                })
        
        return differences
