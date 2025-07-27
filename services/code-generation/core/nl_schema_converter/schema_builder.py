"""
Schema building utilities for converting extracted data to database schemas
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from models.schemas import TableInfo, ColumnInfo, Relationship, SchemaResponse, SchemaMetadata
from .models import (
    ExtractedEntity, ExtractedRelationship, FieldInfo, StandardFields,
    EntityType, RelationshipType, TypeInference, normalize_field_name
)

logger = logging.getLogger(__name__)


class SchemaBuilder:
    """
    Builds database schemas from extracted entities, relationships, and fields
    """
    
    def __init__(self):
        self.standard_fields = StandardFields()
        self.type_inference = TypeInference()
    
    def build_schema_from_extracted_data(
        self,
        entities: List[ExtractedEntity],
        relationships: List[ExtractedRelationship],
        fields: Dict[str, List[FieldInfo]],
        description: str,
        options: Optional[Dict[str, Any]] = None
    ) -> SchemaResponse:
        """
        Build complete schema from extracted data
        
        Args:
            entities: Extracted entities
            relationships: Extracted relationships
            fields: Extracted fields by entity
            description: Original description
            options: Build options
            
        Returns:
            Complete schema response
        """
        options = options or {}
        
        logger.info(f"Building schema from {len(entities)} entities, {len(relationships)} relationships")
        
        # Build tables
        tables = self.build_tables_from_entities(entities, fields, options)
        
        # Build relationships and add foreign keys
        schema_relationships = self.build_relationships_from_extracted(relationships, tables)
        
        # Add foreign key columns to tables
        self._add_foreign_key_columns(tables, schema_relationships)
        
        # Create metadata
        metadata = SchemaMetadata(
            version="1.0",
            created_at=datetime.utcnow().isoformat(),
            description=f"Generated from: {description[:200]}...",
            source="pattern_extraction",
            options=options
        )
        
        schema = SchemaResponse(
            tables=tables,
            relationships=schema_relationships,
            metadata=metadata
        )
        
        logger.info(f"Built schema with {len(tables)} tables and {len(schema_relationships)} relationships")
        return schema
    
    def build_tables_from_entities(
        self,
        entities: List[ExtractedEntity],
        fields: Dict[str, List[FieldInfo]],
        options: Optional[Dict[str, Any]] = None
    ) -> List[TableInfo]:
        """
        Build table definitions from entities
        
        Args:
            entities: List of extracted entities
            fields: Fields by entity name
            options: Build options
            
        Returns:
            List of table definitions
        """
        options = options or {}
        include_timestamps = options.get('include_timestamps', True)
        include_soft_delete = options.get('include_soft_delete', False)
        
        tables = []
        
        for entity in entities:
            # Get standard fields for entity type
            standard_fields = self.standard_fields.get_fields_for_entity_type(entity.entity_type)
            
            # Convert standard fields to ColumnInfo
            columns = []
            for field in standard_fields:
                column = ColumnInfo(
                    name=field.name,
                    type=field.inferred_type,
                    nullable=field.nullable,
                    is_primary_key=field.is_primary_key,
                    unique=getattr(field, 'unique', False),
                    default=field.default,
                    description=field.description,
                    validation=field.validation,
                    max_length=getattr(field, 'max_length', None)
                )
                columns.append(column)
            
            # Add entity-specific fields
            entity_fields = fields.get(entity.name, [])
            for field in entity_fields:
                # Skip if field already exists (avoid duplicates)
                if not any(col.name == field.name for col in columns):
                    column = ColumnInfo(
                        name=field.name,
                        type=field.inferred_type,
                        nullable=field.nullable,
                        is_primary_key=field.is_primary_key,
                        unique=getattr(field, 'unique', False),
                        default=field.default,
                        description=field.description,
                        validation=field.validation,
                        max_length=getattr(field, 'max_length', None)
                    )
                    columns.append(column)
            
            # Add soft delete column if requested
            if include_soft_delete:
                if not any(col.name == 'deleted_at' for col in columns):
                    columns.append(ColumnInfo(
                        name="deleted_at",
                        type="DateTime",
                        nullable=True,
                        description="Soft delete timestamp"
                    ))
            
            # Extract primary keys
            primary_keys = [col.name for col in columns if col.is_primary_key]
            if not primary_keys:
                primary_keys = ['id']  # Default primary key
            
            # Create table
            table = TableInfo(
                name=entity.name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=[],  # Will be populated later
                description=f"Table for managing {entity.name} data",
                indexes=[]  # Will be populated if requested
            )
            
            tables.append(table)
        
        # Add indexes if requested
        if options.get('include_indexes', False):
            self._add_default_indexes(tables)
        
        return tables
    
    def build_relationships_from_extracted(
        self,
        relationships: List[ExtractedRelationship],
        tables: List[TableInfo]
    ) -> List[Relationship]:
        """
        Build relationship definitions from extracted relationships
        
        Args:
            relationships: Extracted relationships
            tables: Table definitions
            
        Returns:
            List of relationship definitions
        """
        schema_relationships = []
        table_names = {table.name for table in tables}
        
        for rel in relationships:
            # Ensure both tables exist
            if rel.source not in table_names or rel.target not in table_names:
                logger.warning(f"Skipping relationship {rel.source} -> {rel.target}: tables not found")
                continue
            
            # Determine relationship columns
            if rel.relationship_type == RelationshipType.MANY_TO_MANY:
                # Many-to-many relationships need junction tables
                junction_relationships = self._create_many_to_many_relationship(rel, tables)
                schema_relationships.extend(junction_relationships)
            else:
                # Direct relationship
                source_column, target_column = self._determine_relationship_columns(rel)
                
                schema_relationship = Relationship(
                    source_table=rel.source,
                    source_column=source_column,
                    target_table=rel.target,
                    target_column=target_column,
                    type=rel.relationship_type.value
                )
                schema_relationships.append(schema_relationship)
        
        return schema_relationships
    
    def enhance_tables_with_business_logic(
        self,
        tables: List[TableInfo],
        description: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[TableInfo]:
        """
        Enhance tables with business logic-specific fields
        
        Args:
            tables: Existing tables
            description: Original description
            options: Enhancement options
            
        Returns:
            Enhanced tables
        """
        # Add common business fields based on description analysis
        description_lower = description.lower()
        
        for table in tables:
            table_name = table.name.lower()
            
            # Add audit fields for important entities
            if any(keyword in description_lower for keyword in ['audit', 'track', 'history', 'log']):
                self._add_audit_fields(table)
            
            # Add status fields for workflow entities
            if any(keyword in description_lower for keyword in ['status', 'state', 'workflow', 'process']):
                if not any(col.name == 'status' for col in table.columns):
                    table.columns.append(ColumnInfo(
                        name="status",
                        type="String",
                        nullable=False,
                        default="active",
                        description=f"Status of the {table_name}"
                    ))
            
            # Add version fields for versioned entities
            if any(keyword in description_lower for keyword in ['version', 'revision', 'draft']):
                if not any(col.name == 'version' for col in table.columns):
                    table.columns.append(ColumnInfo(
                        name="version",
                        type="Integer",
                        nullable=False,
                        default=1,
                        description=f"Version number of the {table_name}"
                    ))
            
            # Add sorting/ordering fields
            if any(keyword in description_lower for keyword in ['order', 'sort', 'priority', 'rank']):
                if not any(col.name in ['sort_order', 'priority', 'rank'] for col in table.columns):
                    table.columns.append(ColumnInfo(
                        name="sort_order",
                        type="Integer",
                        nullable=True,
                        description=f"Sort order for {table_name}"
                    ))
        
        return tables
    
    def _determine_relationship_columns(
        self,
        relationship: ExtractedRelationship
    ) -> tuple[str, str]:
        """Determine source and target columns for relationship"""
        if relationship.relationship_type == RelationshipType.ONE_TO_MANY:
            # Foreign key goes on the "many" side (target)
            return f"{relationship.source}_id", "id"
        elif relationship.relationship_type == RelationshipType.MANY_TO_ONE:
            # Foreign key goes on the "many" side (source)
            return f"{relationship.target}_id", "id"
        elif relationship.relationship_type == RelationshipType.ONE_TO_ONE:
            # Foreign key can go on either side, choose source
            return f"{relationship.target}_id", "id"
        else:
            # Default case
            return f"{relationship.target}_id", "id"
    
    def _create_many_to_many_relationship(
        self,
        relationship: ExtractedRelationship,
        tables: List[TableInfo]
    ) -> List[Relationship]:
        """Create junction table and relationships for many-to-many"""
        # Create junction table name
        junction_name = f"{relationship.source}_{relationship.target}"
        
        # Create junction table columns
        junction_columns = [
            ColumnInfo(
                name="id",
                type="Integer",
                nullable=False,
                is_primary_key=True,
                description="Junction table primary key"
            ),
            ColumnInfo(
                name=f"{relationship.source}_id",
                type="Integer",
                nullable=False,
                description=f"Reference to {relationship.source}"
            ),
            ColumnInfo(
                name=f"{relationship.target}_id", 
                type="Integer",
                nullable=False,
                description=f"Reference to {relationship.target}"
            ),
            ColumnInfo(
                name="created_at",
                type="DateTime",
                nullable=False,
                default="now()",
                description="Association creation timestamp"
            )
        ]
        
        # Create junction table
        junction_table = TableInfo(
            name=junction_name,
            columns=junction_columns,
            primary_keys=["id"],
            foreign_keys=[f"{relationship.source}.id", f"{relationship.target}.id"],
            description=f"Junction table for {relationship.source} and {relationship.target}"
        )
        
        # Add junction table to tables list
        tables.append(junction_table)
        
        # Create relationships
        relationships = [
            Relationship(
                source_table=junction_name,
                source_column=f"{relationship.source}_id",
                target_table=relationship.source,
                target_column="id",
                type="many-to-one"
            ),
            Relationship(
                source_table=junction_name,
                source_column=f"{relationship.target}_id",
                target_table=relationship.target,
                target_column="id",
                type="many-to-one"
            )
        ]
        
        return relationships
    
    def _add_foreign_key_columns(
        self,
        tables: List[TableInfo],
        relationships: List[Relationship]
    ):
        """Add foreign key columns to tables based on relationships"""
        table_map = {table.name: table for table in tables}
        
        for relationship in relationships:
            source_table = table_map.get(relationship.source_table)
            if not source_table:
                continue
            
            # Check if foreign key column already exists
            fk_column_exists = any(
                col.name == relationship.source_column 
                for col in source_table.columns
            )
            
            if not fk_column_exists:
                # Add foreign key column
                fk_column = ColumnInfo(
                    name=relationship.source_column,
                    type="Integer",
                    nullable=True,  # Foreign keys are typically nullable
                    description=f"Foreign key reference to {relationship.target_table}"
                )
                source_table.columns.append(fk_column)
                
                # Add to foreign keys list
                if f"{relationship.target_table}.{relationship.target_column}" not in source_table.foreign_keys:
                    source_table.foreign_keys.append(f"{relationship.target_table}.{relationship.target_column}")
    
    def _add_default_indexes(self, tables: List[TableInfo]):
        """Add default indexes to tables"""
        for table in tables:
            indexes = []
            
            # Index on foreign keys
            for fk in table.foreign_keys:
                fk_column = fk.split('.')[0] + '_id'  # Extract column name
                if any(col.name == fk_column for col in table.columns):
                    indexes.append(f"idx_{table.name}_{fk_column}")
            
            # Index on common searchable fields
            for column in table.columns:
                if (column.name in ['email', 'username', 'name', 'title'] or 
                    column.unique or 
                    column.validation == 'email'):
                    indexes.append(f"idx_{table.name}_{column.name}")
            
            # Index on timestamp fields for sorting
            for column in table.columns:
                if column.type == 'DateTime' and column.name in ['created_at', 'updated_at']:
                    indexes.append(f"idx_{table.name}_{column.name}")
            
            table.indexes = list(set(indexes))  # Remove duplicates
    
    def _add_audit_fields(self, table: TableInfo):
        """Add audit fields to table"""
        audit_fields = [
            ('created_by', 'Integer', 'User who created the record'),
            ('updated_by', 'Integer', 'User who last updated the record'),
            ('version', 'Integer', 'Record version for optimistic locking')
        ]
        
        for field_name, field_type, description in audit_fields:
            if not any(col.name == field_name for col in table.columns):
                table.columns.append(ColumnInfo(
                    name=field_name,
                    type=field_type,
                    nullable=True,
                    description=description
                ))
    
    def validate_schema(self, schema: SchemaResponse) -> List[str]:
        """
        Validate schema and return list of issues
        
        Args:
            schema: Schema to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        table_names = {table.name for table in schema.tables}
        
        # Check tables
        for table in schema.tables:
            # Check if table has primary key
            if not table.primary_keys:
                issues.append(f"Table '{table.name}' has no primary key")
            
            # Check for duplicate column names
            column_names = [col.name for col in table.columns]
            if len(column_names) != len(set(column_names)):
                issues.append(f"Table '{table.name}' has duplicate column names")
            
            # Check column types
            for column in table.columns:
                if not column.type:
                    issues.append(f"Column '{table.name}.{column.name}' has no type")
        
        # Check relationships
        for relationship in schema.relationships:
            # Check if referenced tables exist
            if relationship.source_table not in table_names:
                issues.append(f"Relationship references non-existent source table '{relationship.source_table}'")
            
            if relationship.target_table not in table_names:
                issues.append(f"Relationship references non-existent target table '{relationship.target_table}'")
        
        return issues
    
    def optimize_schema(self, schema: SchemaResponse) -> SchemaResponse:
        """
        Optimize schema for performance and best practices
        
        Args:
            schema: Schema to optimize
            
        Returns:
            Optimized schema
        """
        # Add missing indexes
        for table in schema.tables:
            if not table.indexes:
                self._add_default_indexes([table])
        
        # Optimize data types
        for table in schema.tables:
            for column in table.columns:
                # Optimize string lengths
                if column.type == 'String' and not column.max_length:
                    if column.name in ['email', 'url']:
                        column.max_length = 255
                    elif column.name in ['name', 'title']:
                        column.max_length = 100
                    elif column.name in ['phone']:
                        column.max_length = 20
                    else:
                        column.max_length = 255
        
        return schema
