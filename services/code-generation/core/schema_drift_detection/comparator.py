"""
Schema comparison utilities for detecting differences between schemas
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import uuid

from models.schemas import SchemaResponse, TableInfo, ColumnInfo

from .models import (
    SchemaChange, ChangeType, ChangeSeverity, ComparisonResult,
    ImpactAnalysis
)

logger = logging.getLogger(__name__)


class SchemaComparator:
    """
    Utility class for comparing schemas and detecting changes
    """
    
    def __init__(self):
        self.severity_rules = self._initialize_severity_rules()
    
    def compare_schemas(
        self, 
        old_schema: SchemaResponse, 
        new_schema: SchemaResponse,
        database_name: str = ""
    ) -> ComparisonResult:
        """
        Compare two schemas and return detailed change analysis
        
        Args:
            old_schema: Previous schema
            new_schema: Current schema
            database_name: Name of database being compared
            
        Returns:
            Detailed comparison result
        """
        changes = []
        
        # Detect all types of changes
        changes.extend(self._detect_table_changes(old_schema, new_schema, database_name))
        changes.extend(self._detect_column_changes(old_schema, new_schema, database_name))
        changes.extend(self._detect_relationship_changes(old_schema, new_schema, database_name))
        changes.extend(self._detect_index_changes(old_schema, new_schema, database_name))
        changes.extend(self._detect_constraint_changes(old_schema, new_schema, database_name))
        
        # Create summary
        summary = self._create_change_summary(changes)
        
        return ComparisonResult(
            changes=changes,
            summary=summary
        )
    
    def _detect_table_changes(
        self, 
        old_schema: SchemaResponse, 
        new_schema: SchemaResponse,
        database_name: str
    ) -> List[SchemaChange]:
        """Detect table-level changes"""
        
        changes = []
        old_tables = {table.name: table for table in old_schema.tables}
        new_tables = {table.name: table for table in new_schema.tables}
        
        # Detect added tables
        for table_name in new_tables.keys() - old_tables.keys():
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.TABLE_ADDED,
                severity=ChangeSeverity.MEDIUM,
                object_name=table_name,
                table_name=table_name,
                database_name=database_name,
                details={
                    'table': new_tables[table_name].dict(),
                    'column_count': len(new_tables[table_name].columns)
                }
            ))
        
        # Detect removed tables
        for table_name in old_tables.keys() - new_tables.keys():
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.TABLE_REMOVED,
                severity=ChangeSeverity.CRITICAL,
                object_name=table_name,
                table_name=table_name,
                database_name=database_name,
                details={
                    'table': old_tables[table_name].dict(),
                    'column_count': len(old_tables[table_name].columns)
                }
            ))
        
        # Detect table renames (heuristic based on column similarity)
        added_tables = new_tables.keys() - old_tables.keys()
        removed_tables = old_tables.keys() - new_tables.keys()
        
        for new_table_name in added_tables:
            for old_table_name in removed_tables:
                similarity = self._calculate_table_similarity(
                    old_tables[old_table_name], 
                    new_tables[new_table_name]
                )
                
                if similarity > 0.8:  # High similarity suggests rename
                    changes.append(SchemaChange(
                        change_id=str(uuid.uuid4()),
                        change_type=ChangeType.TABLE_RENAMED,
                        severity=ChangeSeverity.HIGH,
                        object_name=f"{old_table_name} -> {new_table_name}",
                        table_name=new_table_name,
                        database_name=database_name,
                        old_value=old_table_name,
                        new_value=new_table_name,
                        details={
                            'old_table': old_tables[old_table_name].dict(),
                            'new_table': new_tables[new_table_name].dict(),
                            'similarity': similarity
                        }
                    ))
                    
                    # Remove from added/removed to avoid duplicate detection
                    added_tables.remove(new_table_name)
                    removed_tables.remove(old_table_name)
                    break
        
        return changes
    
    def _detect_column_changes(
        self, 
        old_schema: SchemaResponse, 
        new_schema: SchemaResponse,
        database_name: str
    ) -> List[SchemaChange]:
        """Detect column-level changes"""
        
        changes = []
        old_tables = {table.name: table for table in old_schema.tables}
        new_tables = {table.name: table for table in new_schema.tables}
        
        # Check tables that exist in both schemas
        for table_name in old_tables.keys() & new_tables.keys():
            old_table = old_tables[table_name]
            new_table = new_tables[table_name]
            
            old_columns = {col.name: col for col in old_table.columns}
            new_columns = {col.name: col for col in new_table.columns}
            
            # Detect added columns
            for col_name in new_columns.keys() - old_columns.keys():
                changes.append(SchemaChange(
                    change_id=str(uuid.uuid4()),
                    change_type=ChangeType.COLUMN_ADDED,
                    severity=ChangeSeverity.LOW,
                    object_name=f"{table_name}.{col_name}",
                    table_name=table_name,
                    column_name=col_name,
                    database_name=database_name,
                    details={
                        'column': new_columns[col_name].dict()
                    }
                ))
            
            # Detect removed columns
            for col_name in old_columns.keys() - new_columns.keys():
                changes.append(SchemaChange(
                    change_id=str(uuid.uuid4()),
                    change_type=ChangeType.COLUMN_REMOVED,
                    severity=ChangeSeverity.HIGH,
                    object_name=f"{table_name}.{col_name}",
                    table_name=table_name,
                    column_name=col_name,
                    database_name=database_name,
                    details={
                        'column': old_columns[col_name].dict()
                    }
                ))
            
            # Detect modified columns
            for col_name in old_columns.keys() & new_columns.keys():
                old_col = old_columns[col_name]
                new_col = new_columns[col_name]
                
                column_changes = self._detect_column_modifications(
                    old_col, new_col, table_name, database_name
                )
                changes.extend(column_changes)
            
            # Detect column renames
            changes.extend(self._detect_column_renames(
                old_columns, new_columns, table_name, database_name
            ))
        
        return changes
    
    def _detect_column_modifications(
        self,
        old_col: ColumnInfo,
        new_col: ColumnInfo,
        table_name: str,
        database_name: str
    ) -> List[SchemaChange]:
        """Detect specific column modifications"""
        
        changes = []
        modifications = []
        
        # Check data type changes
        if old_col.type != new_col.type:
            modifications.append({
                'property': 'type',
                'old_value': old_col.type,
                'new_value': new_col.type
            })
        
        # Check nullability changes
        if old_col.nullable != new_col.nullable:
            modifications.append({
                'property': 'nullable',
                'old_value': old_col.nullable,
                'new_value': new_col.nullable
            })
        
        # Check primary key changes
        if old_col.is_primary_key != new_col.is_primary_key:
            modifications.append({
                'property': 'is_primary_key',
                'old_value': old_col.is_primary_key,
                'new_value': new_col.is_primary_key
            })
        
        # Check default value changes
        if old_col.default != new_col.default:
            modifications.append({
                'property': 'default',
                'old_value': old_col.default,
                'new_value': new_col.default
            })
        
        # Check unique constraint changes
        old_unique = getattr(old_col, 'unique', False)
        new_unique = getattr(new_col, 'unique', False)
        if old_unique != new_unique:
            modifications.append({
                'property': 'unique',
                'old_value': old_unique,
                'new_value': new_unique
            })
        
        # Create change records for each modification
        for modification in modifications:
            severity = self._determine_modification_severity(modification)
            
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.COLUMN_MODIFIED,
                severity=severity,
                object_name=f"{table_name}.{new_col.name}",
                table_name=table_name,
                column_name=new_col.name,
                database_name=database_name,
                old_value=modification['old_value'],
                new_value=modification['new_value'],
                details={
                    'property': modification['property'],
                    'old_column': old_col.dict(),
                    'new_column': new_col.dict()
                }
            ))
        
        return changes
    
    def _detect_column_renames(
        self,
        old_columns: Dict[str, ColumnInfo],
        new_columns: Dict[str, ColumnInfo],
        table_name: str,
        database_name: str
    ) -> List[SchemaChange]:
        """Detect column renames using similarity heuristics"""
        
        changes = []
        added_columns = set(new_columns.keys()) - set(old_columns.keys())
        removed_columns = set(old_columns.keys()) - set(new_columns.keys())
        
        for new_col_name in added_columns.copy():
            for old_col_name in removed_columns.copy():
                similarity = self._calculate_column_similarity(
                    old_columns[old_col_name],
                    new_columns[new_col_name]
                )
                
                if similarity > 0.9:  # Very high similarity suggests rename
                    changes.append(SchemaChange(
                        change_id=str(uuid.uuid4()),
                        change_type=ChangeType.COLUMN_RENAMED,
                        severity=ChangeSeverity.MEDIUM,
                        object_name=f"{table_name}.{old_col_name} -> {new_col_name}",
                        table_name=table_name,
                        column_name=new_col_name,
                        database_name=database_name,
                        old_value=old_col_name,
                        new_value=new_col_name,
                        details={
                            'old_column': old_columns[old_col_name].dict(),
                            'new_column': new_columns[new_col_name].dict(),
                            'similarity': similarity
                        }
                    ))
                    
                    # Remove from sets to avoid duplicate detection
                    added_columns.remove(new_col_name)
                    removed_columns.remove(old_col_name)
                    break
        
        return changes
    
    def _detect_relationship_changes(
        self, 
        old_schema: SchemaResponse, 
        new_schema: SchemaResponse,
        database_name: str
    ) -> List[SchemaChange]:
        """Detect relationship changes"""
        
        changes = []
        old_relationships = self._normalize_relationships(old_schema.relationships or [])
        new_relationships = self._normalize_relationships(new_schema.relationships or [])
        
        # Detect added relationships
        for rel_key in new_relationships.keys() - old_relationships.keys():
            rel = new_relationships[rel_key]
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.FOREIGN_KEY_ADDED,
                severity=ChangeSeverity.MEDIUM,
                object_name=f"{rel['source_table']}.{rel['source_column']} -> {rel['target_table']}.{rel['target_column']}",
                database_name=database_name,
                details={'relationship': rel}
            ))
        
        # Detect removed relationships
        for rel_key in old_relationships.keys() - new_relationships.keys():
            rel = old_relationships[rel_key]
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.FOREIGN_KEY_REMOVED,
                severity=ChangeSeverity.HIGH,
                object_name=f"{rel['source_table']}.{rel['source_column']} -> {rel['target_table']}.{rel['target_column']}",
                database_name=database_name,
                details={'relationship': rel}
            ))
        
        return changes
    
    def _detect_index_changes(
        self, 
        old_schema: SchemaResponse, 
        new_schema: SchemaResponse,
        database_name: str
    ) -> List[SchemaChange]:
        """Detect index changes"""
        
        changes = []
        
        # Get indexes from table definitions
        old_indexes = self._extract_indexes_from_schema(old_schema)
        new_indexes = self._extract_indexes_from_schema(new_schema)
        
        # Detect added indexes
        for idx_name in new_indexes.keys() - old_indexes.keys():
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.INDEX_ADDED,
                severity=ChangeSeverity.LOW,
                object_name=idx_name,
                database_name=database_name,
                details={'index': new_indexes[idx_name]}
            ))
        
        # Detect removed indexes
        for idx_name in old_indexes.keys() - new_indexes.keys():
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.INDEX_REMOVED,
                severity=ChangeSeverity.MEDIUM,
                object_name=idx_name,
                database_name=database_name,
                details={'index': old_indexes[idx_name]}
            ))
        
        return changes
    
    def _detect_constraint_changes(
        self, 
        old_schema: SchemaResponse, 
        new_schema: SchemaResponse,
        database_name: str
    ) -> List[SchemaChange]:
        """Detect constraint changes"""
        
        changes = []
        
        # Extract constraints from schemas
        old_constraints = self._extract_constraints_from_schema(old_schema)
        new_constraints = self._extract_constraints_from_schema(new_schema)
        
        # Detect added constraints
        for constraint_key in new_constraints.keys() - old_constraints.keys():
            constraint = new_constraints[constraint_key]
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.CONSTRAINT_ADDED,
                severity=ChangeSeverity.MEDIUM,
                object_name=constraint_key,
                database_name=database_name,
                details={'constraint': constraint}
            ))
        
        # Detect removed constraints
        for constraint_key in old_constraints.keys() - new_constraints.keys():
            constraint = old_constraints[constraint_key]
            changes.append(SchemaChange(
                change_id=str(uuid.uuid4()),
                change_type=ChangeType.CONSTRAINT_REMOVED,
                severity=ChangeSeverity.HIGH,
                object_name=constraint_key,
                database_name=database_name,
                details={'constraint': constraint}
            ))
        
        return changes
    
    def _calculate_table_similarity(self, old_table: TableInfo, new_table: TableInfo) -> float:
        """Calculate similarity between two tables based on columns"""
        
        old_column_names = {col.name for col in old_table.columns}
        new_column_names = {col.name for col in new_table.columns}
        
        if not old_column_names and not new_column_names:
            return 1.0
        
        intersection = old_column_names & new_column_names
        union = old_column_names | new_column_names
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_column_similarity(self, old_col: ColumnInfo, new_col: ColumnInfo) -> float:
        """Calculate similarity between two columns"""
        
        similarity_score = 0.0
        total_factors = 5
        
        # Type similarity
        if old_col.type == new_col.type:
            similarity_score += 1.0
        
        # Nullability similarity
        if old_col.nullable == new_col.nullable:
            similarity_score += 1.0
        
        # Primary key similarity
        if old_col.is_primary_key == new_col.is_primary_key:
            similarity_score += 1.0
        
        # Default value similarity
        if old_col.default == new_col.default:
            similarity_score += 1.0
        
        # Unique constraint similarity
        old_unique = getattr(old_col, 'unique', False)
        new_unique = getattr(new_col, 'unique', False)
        if old_unique == new_unique:
            similarity_score += 1.0
        
        return similarity_score / total_factors
    
    def _normalize_relationships(self, relationships) -> Dict[str, Dict]:
        """Normalize relationships to a comparable format"""
        
        normalized = {}
        for rel in relationships:
            key = f"{rel.source_table}.{rel.source_column}->{rel.target_table}.{rel.target_column}"
            normalized[key] = {
                'source_table': rel.source_table,
                'source_column': rel.source_column,
                'target_table': rel.target_table,
                'target_column': rel.target_column,
                'type': rel.type
            }
        return normalized
    
    def _extract_indexes_from_schema(self, schema: SchemaResponse) -> Dict[str, Dict]:
        """Extract indexes from schema tables"""
        
        indexes = {}
        for table in schema.tables:
            for index_name in (table.indexes or []):
                indexes[index_name] = {
                    'name': index_name,
                    'table': table.name
                }
        return indexes
    
    def _extract_constraints_from_schema(self, schema: SchemaResponse) -> Dict[str, Dict]:
        """Extract constraints from schema"""
        
        constraints = {}
        
        for table in schema.tables:
            # Primary key constraints
            if table.primary_keys:
                constraint_key = f"{table.name}_pk"
                constraints[constraint_key] = {
                    'type': 'primary_key',
                    'table': table.name,
                    'columns': table.primary_keys
                }
            
            # Foreign key constraints
            for fk in (table.foreign_keys or []):
                constraint_key = f"{table.name}_{fk}"
                constraints[constraint_key] = {
                    'type': 'foreign_key',
                    'table': table.name,
                    'reference': fk
                }
            
            # Unique constraints (from columns)
            for col in table.columns:
                if getattr(col, 'unique', False):
                    constraint_key = f"{table.name}_{col.name}_unique"
                    constraints[constraint_key] = {
                        'type': 'unique',
                        'table': table.name,
                        'column': col.name
                    }
        
        return constraints
    
    def _determine_modification_severity(self, modification: Dict) -> ChangeSeverity:
        """Determine severity of a column modification"""
        
        property_name = modification['property']
        old_value = modification['old_value']
        new_value = modification['new_value']
        
        if property_name == 'type':
            return ChangeSeverity.CRITICAL
        elif property_name == 'nullable':
            if old_value and not new_value:  # Making non-nullable
                return ChangeSeverity.HIGH
            else:
                return ChangeSeverity.MEDIUM
        elif property_name == 'is_primary_key':
            return ChangeSeverity.CRITICAL
        elif property_name == 'unique':
            return ChangeSeverity.MEDIUM
        elif property_name == 'default':
            return ChangeSeverity.LOW
        else:
            return ChangeSeverity.MEDIUM
    
    def _create_change_summary(self, changes: List[SchemaChange]) -> Dict[str, int]:
        """Create summary of changes by type"""
        
        summary = {}
        for change_type in ChangeType:
            summary[change_type.value] = 0
        
        for change in changes:
            summary[change.change_type.value] += 1
        
        return summary
    
    def _initialize_severity_rules(self) -> Dict[ChangeType, ChangeSeverity]:
        """Initialize default severity rules for change types"""
        
        return {
            ChangeType.TABLE_ADDED: ChangeSeverity.MEDIUM,
            ChangeType.TABLE_REMOVED: ChangeSeverity.CRITICAL,
            ChangeType.TABLE_RENAMED: ChangeSeverity.HIGH,
            ChangeType.COLUMN_ADDED: ChangeSeverity.LOW,
            ChangeType.COLUMN_REMOVED: ChangeSeverity.HIGH,
            ChangeType.COLUMN_MODIFIED: ChangeSeverity.MEDIUM,
            ChangeType.COLUMN_RENAMED: ChangeSeverity.MEDIUM,
            ChangeType.INDEX_ADDED: ChangeSeverity.LOW,
            ChangeType.INDEX_REMOVED: ChangeSeverity.MEDIUM,
            ChangeType.CONSTRAINT_ADDED: ChangeSeverity.MEDIUM,
            ChangeType.CONSTRAINT_REMOVED: ChangeSeverity.HIGH,
            ChangeType.PRIMARY_KEY_ADDED: ChangeSeverity.HIGH,
            ChangeType.PRIMARY_KEY_REMOVED: ChangeSeverity.CRITICAL,
            ChangeType.FOREIGN_KEY_ADDED: ChangeSeverity.MEDIUM,
            ChangeType.FOREIGN_KEY_REMOVED: ChangeSeverity.HIGH
        }
