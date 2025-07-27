"""
Normalization and best practices analysis
"""
import logging
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime

from models.schemas import SchemaResponse, TableInfo, ColumnInfo, Relationship
from .base import SchemaCritique, CritiqueCategory, SeverityLevel

logger = logging.getLogger(__name__)

class NormalizationAnalyzer:
    """Analyzes schema for normalization and best practices"""
    
    def __init__(self):
        self.reserved_keywords = {
            'user', 'order', 'group', 'table', 'index', 'key', 'where', 'select',
            'from', 'update', 'delete', 'insert', 'create', 'drop', 'alter'
        }
    
    async def analyze_normalization(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Analyze schema normalization"""
        critiques = []
        
        try:
            # Check for 1NF violations
            critiques.extend(await self._check_first_normal_form(schema))
            
            # Check for 2NF violations
            critiques.extend(await self._check_second_normal_form(schema))
            
            # Check for 3NF violations
            critiques.extend(await self._check_third_normal_form(schema))
            
            # Check for BCNF violations
            critiques.extend(await self._check_bcnf(schema))
            
        except Exception as e:
            logger.error(f"Error in normalization analysis: {e}")
        
        return critiques
    
    async def analyze_naming_conventions(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Analyze naming conventions"""
        critiques = []
        
        try:
            # Check table naming
            critiques.extend(await self._check_table_naming(schema))
            
            # Check column naming
            critiques.extend(await self._check_column_naming(schema))
            
            # Check for reserved keywords
            critiques.extend(await self._check_reserved_keywords(schema))
            
            # Check naming consistency
            critiques.extend(await self._check_naming_consistency(schema))
            
        except Exception as e:
            logger.error(f"Error in naming convention analysis: {e}")
        
        return critiques
    
    async def analyze_data_types(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Analyze data type usage"""
        critiques = []
        
        try:
            # Check for appropriate data types
            critiques.extend(await self._check_data_type_appropriateness(schema))
            
            # Check for missing constraints
            critiques.extend(await self._check_missing_constraints(schema))
            
        except Exception as e:
            logger.error(f"Error in data type analysis: {e}")
        
        return critiques
    
    async def _check_first_normal_form(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check for 1NF violations (atomic values)"""
        critiques = []
        
        for table in schema.tables:
            for column in table.columns:
                # Check for columns that might store multiple values
                if self._suggests_multiple_values(column.name, column.type):
                    critiques.append(SchemaCritique(
                        id=str(uuid.uuid4()),
                        category=CritiqueCategory.NORMALIZATION,
                        severity=SeverityLevel.MEDIUM,
                        title="Potential 1NF Violation",
                        description=f"Column '{column.name}' in table '{table.name}' may store multiple values",
                        recommendation="Consider normalizing into a separate table with a one-to-many relationship",
                        affected_tables=[table.name],
                        affected_columns=[f"{table.name}.{column.name}"],
                        confidence=0.6,
                        impact_score=0.7,
                        fix_complexity="medium",
                        estimated_effort="1-2 hours",
                        references=["https://en.wikipedia.org/wiki/First_normal_form"],
                        code_examples=[
                            f"CREATE TABLE {table.name}_{column.name} (",
                            f"  {table.name}_id INT,",
                            f"  {column.name}_value VARCHAR(255),",
                            f"  PRIMARY KEY ({table.name}_id, {column.name}_value)",
                            ");"
                        ],
                        created_at=datetime.now()
                    ))
        
        return critiques
    
    def _suggests_multiple_values(self, column_name: str, column_type: str) -> bool:
        """Check if column name/type suggests multiple values"""
        multi_value_indicators = [
            'tags', 'categories', 'skills', 'hobbies', 'interests',
            'permissions', 'roles', 'addresses', 'phones', 'emails'
        ]
        
        column_lower = column_name.lower()
        
        # Check for plural nouns that might indicate multiple values
        for indicator in multi_value_indicators:
            if indicator in column_lower:
                return True
        
        # Check for JSON/TEXT types that might store arrays
        if column_type.upper() in ['JSON', 'JSONB', 'TEXT'] and any(
            word in column_lower for word in ['list', 'array', 'multiple']
        ):
            return True
        
        return False
    
    async def _check_second_normal_form(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check for 2NF violations (partial dependencies)"""
        critiques = []
        
        for table in schema.tables:
            # Look for composite primary keys
            pk_columns = [col for col in table.columns if getattr(col, 'primary_key', False)]
            
            if len(pk_columns) > 1:
                # Check for columns that depend on only part of the primary key
                non_pk_columns = [col for col in table.columns if not getattr(col, 'primary_key', False)]
                
                for column in non_pk_columns:
                    if self._suggests_partial_dependency(column.name, pk_columns):
                        critiques.append(SchemaCritique(
                            id=str(uuid.uuid4()),
                            category=CritiqueCategory.NORMALIZATION,
                            severity=SeverityLevel.MEDIUM,
                            title="Potential 2NF Violation",
                            description=f"Column '{column.name}' in table '{table.name}' may depend on only part of the composite primary key",
                            recommendation="Consider moving this column to a separate table with appropriate foreign key relationships",
                            affected_tables=[table.name],
                            affected_columns=[f"{table.name}.{column.name}"],
                            confidence=0.5,
                            impact_score=0.6,
                            fix_complexity="medium",
                            estimated_effort="2-3 hours",
                            references=["https://en.wikipedia.org/wiki/Second_normal_form"],
                            code_examples=[],
                            created_at=datetime.now()
                        ))
        
        return critiques
    
    def _suggests_partial_dependency(self, column_name: str, pk_columns: List[ColumnInfo]) -> bool:
        """Check if column suggests partial dependency on composite PK"""
        # Simple heuristic: if column name contains part of PK column name
        column_lower = column_name.lower()
        
        for pk_col in pk_columns:
            pk_name_lower = pk_col.name.lower().replace('_id', '').replace('id', '')
            if pk_name_lower and pk_name_lower in column_lower:
                return True
        
        return False
    
    async def _check_third_normal_form(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check for 3NF violations (transitive dependencies)"""
        critiques = []
        
        for table in schema.tables:
            # Look for potential transitive dependencies
            for column in table.columns:
                if self._suggests_transitive_dependency(table, column):
                    critiques.append(SchemaCritique(
                        id=str(uuid.uuid4()),
                        category=CritiqueCategory.NORMALIZATION,
                        severity=SeverityLevel.LOW,
                        title="Potential 3NF Violation",
                        description=f"Column '{column.name}' in table '{table.name}' may create a transitive dependency",
                        recommendation="Consider extracting related attributes into a separate table",
                        affected_tables=[table.name],
                        affected_columns=[f"{table.name}.{column.name}"],
                        confidence=0.4,
                        impact_score=0.5,
                        fix_complexity="medium",
                        estimated_effort="2-4 hours",
                        references=["https://en.wikipedia.org/wiki/Third_normal_form"],
                        code_examples=[],
                        created_at=datetime.now()
                    ))
        
        return critiques
    
    def _suggests_transitive_dependency(self, table: TableInfo, column: ColumnInfo) -> bool:
        """Check if column suggests transitive dependency"""
        # Look for related columns that might indicate denormalization
        column_name = column.name.lower()
        
        # Common patterns that suggest transitive dependencies
        related_patterns = [
            ('country', 'country_code'),
            ('state', 'state_code'),
            ('category', 'category_name'),
            ('status', 'status_name'),
            ('type', 'type_name')
        ]
        
        for pattern1, pattern2 in related_patterns:
            if pattern1 in column_name:
                # Check if there's a related column
                for other_col in table.columns:
                    if pattern2 in other_col.name.lower():
                        return True
        
        return False
    
    async def _check_bcnf(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check for BCNF violations"""
        # BCNF analysis is complex and requires deep understanding of functional dependencies
        # For now, we'll provide a simple check
        return []
    
    async def _check_table_naming(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check table naming conventions"""
        critiques = []
        
        naming_patterns = {
            'snake_case': 0,
            'camelCase': 0,
            'PascalCase': 0,
            'lowercase': 0
        }
        
        for table in schema.tables:
            name = table.name
            
            if '_' in name and name.islower():
                naming_patterns['snake_case'] += 1
            elif name[0].islower() and any(c.isupper() for c in name[1:]):
                naming_patterns['camelCase'] += 1
            elif name[0].isupper() and any(c.isupper() for c in name[1:]):
                naming_patterns['PascalCase'] += 1
            elif name.islower() and '_' not in name:
                naming_patterns['lowercase'] += 1
        
        # Check for consistency
        total_tables = len(schema.tables)
        max_pattern = max(naming_patterns.values())
        
        if max_pattern < total_tables * 0.8:  # Less than 80% consistency
            critiques.append(SchemaCritique(
                id=str(uuid.uuid4()),
                category=CritiqueCategory.NAMING_CONVENTIONS,
                severity=SeverityLevel.LOW,
                title="Inconsistent Table Naming",
                description="Table names use inconsistent naming conventions",
                recommendation="Adopt a consistent naming convention (e.g., snake_case) for all tables",
                affected_tables=[table.name for table in schema.tables],
                affected_columns=[],
                confidence=0.8,
                impact_score=0.3,
                fix_complexity="easy",
                estimated_effort="30 minutes",
                references=["https://www.sqlstyle.guide/"],
                code_examples=[],
                created_at=datetime.now()
            ))
        
        return critiques
    
    async def _check_column_naming(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check column naming conventions"""
        critiques = []
        
        for table in schema.tables:
            for column in table.columns:
                # Check for ambiguous column names
                if column.name.lower() in ['id', 'name', 'data', 'info', 'value']:
                    critiques.append(SchemaCritique(
                        id=str(uuid.uuid4()),
                        category=CritiqueCategory.NAMING_CONVENTIONS,
                        severity=SeverityLevel.LOW,
                        title="Ambiguous Column Name",
                        description=f"Column '{column.name}' in table '{table.name}' has an ambiguous name",
                        recommendation=f"Consider using a more descriptive name like '{table.name}_{column.name}' or similar",
                        affected_tables=[table.name],
                        affected_columns=[f"{table.name}.{column.name}"],
                        confidence=0.7,
                        impact_score=0.2,
                        fix_complexity="easy",
                        estimated_effort="5 minutes",
                        references=["https://www.sqlstyle.guide/"],
                        code_examples=[f"ALTER TABLE {table.name} RENAME COLUMN {column.name} TO {table.name}_{column.name};"],
                        created_at=datetime.now()
                    ))
        
        return critiques
    
    async def _check_reserved_keywords(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check for reserved keyword usage"""
        critiques = []
        
        for table in schema.tables:
            if table.name.lower() in self.reserved_keywords:
                critiques.append(SchemaCritique(
                    id=str(uuid.uuid4()),
                    category=CritiqueCategory.NAMING_CONVENTIONS,
                    severity=SeverityLevel.MEDIUM,
                    title="Reserved Keyword Used as Table Name",
                    description=f"Table name '{table.name}' is a reserved keyword",
                    recommendation=f"Rename table to avoid conflicts, e.g., '{table.name}_table' or similar",
                    affected_tables=[table.name],
                    affected_columns=[],
                    confidence=0.9,
                    impact_score=0.6,
                    fix_complexity="medium",
                    estimated_effort="30 minutes",
                    references=["https://dev.mysql.com/doc/refman/8.0/en/keywords.html"],
                    code_examples=[f"ALTER TABLE {table.name} RENAME TO {table.name}_table;"],
                    created_at=datetime.now()
                ))
            
            for column in table.columns:
                if column.name.lower() in self.reserved_keywords:
                    critiques.append(SchemaCritique(
                        id=str(uuid.uuid4()),
                        category=CritiqueCategory.NAMING_CONVENTIONS,
                        severity=SeverityLevel.MEDIUM,
                        title="Reserved Keyword Used as Column Name",
                        description=f"Column name '{column.name}' in table '{table.name}' is a reserved keyword",
                        recommendation=f"Rename column to avoid conflicts",
                        affected_tables=[table.name],
                        affected_columns=[f"{table.name}.{column.name}"],
                        confidence=0.9,
                        impact_score=0.5,
                        fix_complexity="easy",
                        estimated_effort="10 minutes",
                        references=["https://dev.mysql.com/doc/refman/8.0/en/keywords.html"],
                        code_examples=[f"ALTER TABLE {table.name} RENAME COLUMN {column.name} TO {column.name}_field;"],
                        created_at=datetime.now()
                    ))
        
        return critiques
    
    async def _check_naming_consistency(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check overall naming consistency"""
        # This is covered in table naming check
        return []
    
    async def _check_data_type_appropriateness(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check for appropriate data type usage"""
        critiques = []
        
        for table in schema.tables:
            for column in table.columns:
                # Check for inappropriate VARCHAR usage for numeric data
                if column.type.upper().startswith('VARCHAR') and self._suggests_numeric_data(column.name):
                    critiques.append(SchemaCritique(
                        id=str(uuid.uuid4()),
                        category=CritiqueCategory.DATA_TYPES,
                        severity=SeverityLevel.MEDIUM,
                        title="Inappropriate Data Type",
                        description=f"Column '{column.name}' in table '{table.name}' uses VARCHAR but appears to store numeric data",
                        recommendation="Consider using appropriate numeric data type (INT, DECIMAL, etc.)",
                        affected_tables=[table.name],
                        affected_columns=[f"{table.name}.{column.name}"],
                        confidence=0.6,
                        impact_score=0.5,
                        fix_complexity="medium",
                        estimated_effort="30 minutes",
                        references=["https://dev.mysql.com/doc/refman/8.0/en/data-types.html"],
                        code_examples=[],
                        created_at=datetime.now()
                    ))
        
        return critiques
    
    def _suggests_numeric_data(self, column_name: str) -> bool:
        """Check if column name suggests numeric data"""
        numeric_indicators = [
            'amount', 'price', 'cost', 'total', 'count', 'quantity',
            'number', 'num', 'score', 'rating', 'percentage', 'percent'
        ]
        
        column_lower = column_name.lower()
        return any(indicator in column_lower for indicator in numeric_indicators)
    
    async def _check_missing_constraints(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Check for missing constraints"""
        critiques = []
        
        for table in schema.tables:
            # Check for tables without primary keys
            has_pk = any(getattr(col, 'primary_key', False) for col in table.columns)
            if not has_pk:
                critiques.append(SchemaCritique(
                    id=str(uuid.uuid4()),
                    category=CritiqueCategory.CONSTRAINTS,
                    severity=SeverityLevel.HIGH,
                    title="Missing Primary Key",
                    description=f"Table '{table.name}' does not have a primary key",
                    recommendation="Add a primary key to ensure row uniqueness and improve performance",
                    affected_tables=[table.name],
                    affected_columns=[],
                    confidence=0.9,
                    impact_score=0.8,
                    fix_complexity="easy",
                    estimated_effort="15 minutes",
                    references=["https://dev.mysql.com/doc/refman/8.0/en/create-table.html"],
                    code_examples=[f"ALTER TABLE {table.name} ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST;"],
                    created_at=datetime.now()
                ))
        
        return critiques
