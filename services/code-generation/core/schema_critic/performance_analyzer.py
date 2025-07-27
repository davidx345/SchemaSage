"""
Performance analysis for schema critique
"""
import logging
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime

from models.schemas import SchemaResponse, TableInfo, ColumnInfo, Relationship
from .base import SchemaCritique, CritiqueCategory, SeverityLevel

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """Analyzes schema for performance issues"""
    
    def __init__(self):
        self.max_columns_per_table = 50
        self.max_tables_for_small_db = 20
        self.max_index_columns = 5
        self.max_varchar_length = 4000
    
    async def analyze_performance(
        self, 
        schema: SchemaResponse,
        context: Optional[Dict[str, Any]] = None
    ) -> List[SchemaCritique]:
        """Analyze schema for performance issues"""
        critiques = []
        
        try:
            # Analyze table structure
            critiques.extend(await self._analyze_table_structure(schema))
            
            # Analyze column definitions
            critiques.extend(await self._analyze_column_performance(schema))
            
            # Analyze relationships
            critiques.extend(await self._analyze_relationship_performance(schema))
            
            # Analyze potential query performance
            critiques.extend(await self._analyze_query_performance(schema, context))
            
            # Analyze indexing opportunities
            critiques.extend(await self._analyze_indexing_opportunities(schema))
            
        except Exception as e:
            logger.error(f"Error in performance analysis: {e}")
        
        return critiques
    
    async def _analyze_table_structure(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Analyze table structure for performance issues"""
        critiques = []
        
        for table in schema.tables:
            # Check for very wide tables
            if len(table.columns) > self.max_columns_per_table:
                critiques.append(SchemaCritique(
                    id=str(uuid.uuid4()),
                    category=CritiqueCategory.PERFORMANCE,
                    severity=SeverityLevel.HIGH,
                    title="Very Wide Table Detected",
                    description=f"Table '{table.name}' has {len(table.columns)} columns, which may impact query performance",
                    recommendation="Consider vertical partitioning or splitting into multiple related tables",
                    affected_tables=[table.name],
                    affected_columns=[],
                    confidence=0.8,
                    impact_score=0.7,
                    fix_complexity="medium",
                    estimated_effort="2-4 hours",
                    references=["https://docs.microsoft.com/en-us/sql/relational-databases/tables/"],
                    code_examples=[],
                    created_at=datetime.now()
                ))
            
            # Check for tables with too few columns (potential over-normalization)
            if len(table.columns) < 3 and table.name.lower() not in ['log', 'audit', 'session']:
                critiques.append(SchemaCritique(
                    id=str(uuid.uuid4()),
                    category=CritiqueCategory.PERFORMANCE,
                    severity=SeverityLevel.MEDIUM,
                    title="Potentially Over-Normalized Table",
                    description=f"Table '{table.name}' has only {len(table.columns)} columns, which might indicate over-normalization",
                    recommendation="Consider if this table could be merged with related tables to reduce JOIN operations",
                    affected_tables=[table.name],
                    affected_columns=[],
                    confidence=0.6,
                    impact_score=0.4,
                    fix_complexity="medium",
                    estimated_effort="1-2 hours",
                    references=["https://en.wikipedia.org/wiki/Database_normalization"],
                    code_examples=[],
                    created_at=datetime.now()
                ))
        
        # Check total number of tables
        if len(schema.tables) > 100:
            critiques.append(SchemaCritique(
                id=str(uuid.uuid4()),
                category=CritiqueCategory.PERFORMANCE,
                severity=SeverityLevel.MEDIUM,
                title="Large Number of Tables",
                description=f"Schema contains {len(schema.tables)} tables, which may impact maintainability",
                recommendation="Consider grouping related tables into modules or microservices",
                affected_tables=[],
                affected_columns=[],
                confidence=0.7,
                impact_score=0.5,
                fix_complexity="hard",
                estimated_effort="1-2 days",
                references=["https://microservices.io/patterns/data/database-per-service.html"],
                code_examples=[],
                created_at=datetime.now()
            ))
        
        return critiques
    
    async def _analyze_column_performance(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Analyze column definitions for performance issues"""
        critiques = []
        
        for table in schema.tables:
            for column in table.columns:
                # Check for oversized VARCHAR columns
                if column.type.upper().startswith('VARCHAR'):
                    # Extract length if specified
                    if '(' in column.type and ')' in column.type:
                        try:
                            length_str = column.type.split('(')[1].split(')')[0]
                            length = int(length_str)
                            
                            if length > self.max_varchar_length:
                                critiques.append(SchemaCritique(
                                    id=str(uuid.uuid4()),
                                    category=CritiqueCategory.PERFORMANCE,
                                    severity=SeverityLevel.MEDIUM,
                                    title="Oversized VARCHAR Column",
                                    description=f"Column '{column.name}' in table '{table.name}' has VARCHAR({length}), which may waste storage",
                                    recommendation="Consider using TEXT type for large text data or reduce VARCHAR size if appropriate",
                                    affected_tables=[table.name],
                                    affected_columns=[f"{table.name}.{column.name}"],
                                    confidence=0.7,
                                    impact_score=0.4,
                                    fix_complexity="easy",
                                    estimated_effort="15 minutes",
                                    references=["https://dev.mysql.com/doc/refman/8.0/en/storage-requirements.html"],
                                    code_examples=[f"ALTER TABLE {table.name} MODIFY {column.name} TEXT;"],
                                    created_at=datetime.now()
                                ))
                        
                        except (ValueError, IndexError):
                            pass
                
                # Check for potential indexing columns
                if column.name.lower().endswith('_id') and not getattr(column, 'primary_key', False):
                    # This is likely a foreign key that should be indexed
                    pass  # Will be handled in indexing analysis
        
        return critiques
    
    async def _analyze_relationship_performance(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Analyze relationships for performance issues"""
        critiques = []
        
        # Count relationships per table
        table_relationships = {}
        for relationship in schema.relationships:
            from_table = relationship.from_table
            to_table = relationship.to_table
            
            table_relationships[from_table] = table_relationships.get(from_table, 0) + 1
            table_relationships[to_table] = table_relationships.get(to_table, 0) + 1
        
        # Check for tables with too many relationships
        for table_name, rel_count in table_relationships.items():
            if rel_count > 10:
                critiques.append(SchemaCritique(
                    id=str(uuid.uuid4()),
                    category=CritiqueCategory.PERFORMANCE,
                    severity=SeverityLevel.HIGH,
                    title="Table with Many Relationships",
                    description=f"Table '{table_name}' has {rel_count} relationships, which may create complex JOIN operations",
                    recommendation="Consider breaking down the table or using denormalization for frequently accessed data",
                    affected_tables=[table_name],
                    affected_columns=[],
                    confidence=0.8,
                    impact_score=0.7,
                    fix_complexity="hard",
                    estimated_effort="4-8 hours",
                    references=["https://en.wikipedia.org/wiki/Denormalization"],
                    code_examples=[],
                    created_at=datetime.now()
                ))
        
        return critiques
    
    async def _analyze_query_performance(
        self, 
        schema: SchemaResponse, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[SchemaCritique]:
        """Analyze potential query performance issues"""
        critiques = []
        
        # Check for circular dependencies that could cause complex queries
        circular_deps = self._detect_circular_dependencies(schema.relationships)
        if circular_deps:
            critiques.append(SchemaCritique(
                id=str(uuid.uuid4()),
                category=CritiqueCategory.PERFORMANCE,
                severity=SeverityLevel.HIGH,
                title="Circular Dependencies Detected",
                description=f"Circular dependencies found in relationships: {' -> '.join(circular_deps)}",
                recommendation="Break circular dependencies by introducing junction tables or restructuring relationships",
                affected_tables=circular_deps,
                affected_columns=[],
                confidence=0.9,
                impact_score=0.8,
                fix_complexity="hard",
                estimated_effort="4-6 hours",
                references=["https://en.wikipedia.org/wiki/Circular_dependency"],
                code_examples=[],
                created_at=datetime.now()
            ))
        
        return critiques
    
    async def _analyze_indexing_opportunities(self, schema: SchemaResponse) -> List[SchemaCritique]:
        """Analyze indexing opportunities"""
        critiques = []
        
        for table in schema.tables:
            # Check for foreign key columns that might need indexes
            foreign_key_columns = []
            for relationship in schema.relationships:
                if relationship.from_table == table.name:
                    foreign_key_columns.append(relationship.from_column)
            
            for fk_column in foreign_key_columns:
                critiques.append(SchemaCritique(
                    id=str(uuid.uuid4()),
                    category=CritiqueCategory.PERFORMANCE,
                    severity=SeverityLevel.MEDIUM,
                    title="Missing Index on Foreign Key",
                    description=f"Foreign key column '{fk_column}' in table '{table.name}' may benefit from an index",
                    recommendation=f"Consider adding an index on {table.name}.{fk_column} for better JOIN performance",
                    affected_tables=[table.name],
                    affected_columns=[f"{table.name}.{fk_column}"],
                    confidence=0.8,
                    impact_score=0.6,
                    fix_complexity="easy",
                    estimated_effort="5 minutes",
                    references=["https://dev.mysql.com/doc/refman/8.0/en/mysql-indexes.html"],
                    code_examples=[f"CREATE INDEX idx_{table.name}_{fk_column} ON {table.name}({fk_column});"],
                    created_at=datetime.now()
                ))
        
        return critiques
    
    def _detect_circular_dependencies(self, relationships: List[Relationship]) -> Optional[List[str]]:
        """Detect circular dependencies in relationships"""
        # Build adjacency list
        graph = {}
        for rel in relationships:
            if rel.from_table not in graph:
                graph[rel.from_table] = []
            graph[rel.from_table].append(rel.to_table)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                cycle = dfs(neighbor, path + [node])
                if cycle:
                    return cycle
            
            rec_stack.remove(node)
            return None
        
        for node in graph:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    return cycle
        
        return None
