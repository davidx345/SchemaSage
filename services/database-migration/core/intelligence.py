"""
Migration Intelligence Engine
"""
from typing import List, Dict, Any, Optional, Tuple
import openai
from ..models import SchemaInfo, SchemaComparison, DataTypeMapping, MigrationPlan, MigrationStep, RiskAssessment, MigrationStepType
from ..config import AI_CONFIG, RISK_THRESHOLDS, SUPPORTED_DATABASES
import json
import logging

logger = logging.getLogger(__name__)

class MigrationIntelligence:
    """AI-powered migration intelligence engine."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or AI_CONFIG.get("openai_api_key")
        if self.api_key:
            openai.api_key = self.api_key
    
    def analyze_migration_complexity(self, source_schema: SchemaInfo, target_type: str) -> Dict[str, Any]:
        """Analyze migration complexity using AI."""
        complexity_factors = {
            "table_count": len(source_schema.tables),
            "total_columns": sum(len(table.columns) for table in source_schema.tables),
            "data_types_complexity": self._calculate_data_type_complexity(source_schema, target_type),
            "relationship_complexity": self._calculate_relationship_complexity(source_schema),
            "size_complexity": self._calculate_size_complexity(source_schema)
        }
        
        # Calculate overall complexity score (0.0 to 1.0)
        overall_complexity = self._calculate_overall_complexity(complexity_factors)
        
        return {
            "complexity_score": overall_complexity,
            "factors": complexity_factors,
            "risk_level": self._get_risk_level_from_complexity(overall_complexity),
            "estimated_duration_hours": self._estimate_migration_duration(complexity_factors)
        }
    
    def generate_migration_plan(self, source_schema: SchemaInfo, target_type: str, migration_config: Dict[str, Any] = None) -> MigrationPlan:
        """Generate comprehensive migration plan."""
        migration_config = migration_config or {}
        
        # Analyze schemas and create mappings
        data_type_mappings = self.create_data_type_mappings(source_schema, target_type)
        schema_comparison = self.compare_schemas(source_schema, None)  # Comparing with target requirements
        
        # Generate migration steps
        steps = self._generate_migration_steps(source_schema, target_type, data_type_mappings, migration_config)
        
        # Create migration plan
        plan = MigrationPlan(
            plan_id=f"migration_{source_schema.database_type}_to_{target_type}_{len(steps)}steps",
            source_connection_id="source",
            target_connection_id="target", 
            name=f"Migration from {source_schema.database_type} to {target_type}",
            description=f"Automated migration plan for {len(source_schema.tables)} tables",
            steps=steps,
            total_estimated_duration=sum(step.estimated_duration or 0 for step in steps),
            overall_risk_level=self._calculate_plan_risk_level(steps)
        )
        
        return plan
    
    def create_data_type_mappings(self, source_schema: SchemaInfo, target_type: str) -> List[DataTypeMapping]:
        """Create data type mappings between databases."""
        mappings = []
        
        # Get all unique data types from source schema
        source_types = set()
        for table in source_schema.tables:
            for column in table.columns:
                source_types.add(column.data_type.upper())
        
        # Create mappings for each source type
        for source_type in source_types:
            target_type_mapped = self._get_target_data_type(source_type, source_schema.database_type, target_type)
            
            mapping = DataTypeMapping(
                source_type=source_type,
                target_type=target_type_mapped,
                source_database=source_schema.database_type,
                target_database=target_type,
                requires_conversion=self._requires_conversion(source_type, target_type_mapped),
                conversion_notes=self._get_conversion_notes(source_type, target_type_mapped),
                data_loss_risk=self._assess_data_loss_risk(source_type, target_type_mapped)
            )
            mappings.append(mapping)
        
        return mappings
    
    def assess_migration_risks(self, migration_plan: MigrationPlan) -> RiskAssessment:
        """Comprehensive risk assessment for migration."""
        # Calculate various risk factors
        complexity_score = self._calculate_complexity_from_plan(migration_plan)
        data_loss_risk = self._calculate_data_loss_risk(migration_plan)
        downtime_risk = self._calculate_downtime_risk(migration_plan)
        performance_impact = self._calculate_performance_impact(migration_plan)
        
        # Identify critical issues
        breaking_changes = self._identify_breaking_changes(migration_plan)
        critical_warnings = self._identify_critical_warnings(migration_plan)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(migration_plan)
        mitigation_strategies = self._generate_mitigation_strategies(migration_plan)
        
        # Overall risk level
        overall_risk = self._calculate_overall_risk(complexity_score, data_loss_risk, downtime_risk, performance_impact)
        
        return RiskAssessment(
            migration_id=migration_plan.plan_id,
            complexity_score=complexity_score,
            data_loss_risk=data_loss_risk,
            downtime_risk=downtime_risk,
            performance_impact=performance_impact,
            breaking_changes=breaking_changes,
            critical_warnings=critical_warnings,
            recommendations=recommendations,
            mitigation_strategies=mitigation_strategies,
            overall_risk=overall_risk
        )
    
    def optimize_migration_order(self, steps: List[MigrationStep]) -> List[MigrationStep]:
        """Optimize the order of migration steps based on dependencies and risk."""
        # Create dependency graph
        dependency_graph = self._build_dependency_graph(steps)
        
        # Topological sort with risk optimization
        optimized_steps = self._topological_sort_with_risk_optimization(steps, dependency_graph)
        
        return optimized_steps
    
    def generate_rollback_scripts(self, migration_plan: MigrationPlan) -> MigrationPlan:
        """Generate rollback scripts for all migration steps."""
        for step in migration_plan.steps:
            if not step.rollback_script:
                step.rollback_script = self._generate_rollback_script(step)
        
        return migration_plan
    
    def _calculate_data_type_complexity(self, schema: SchemaInfo, target_type: str) -> float:
        """Calculate complexity based on data type conversions."""
        total_columns = sum(len(table.columns) for table in schema.tables)
        if total_columns == 0:
            return 0.0
        
        complex_conversions = 0
        for table in schema.tables:
            for column in table.columns:
                if self._is_complex_data_type_conversion(column.data_type, schema.database_type, target_type):
                    complex_conversions += 1
        
        return min(complex_conversions / total_columns, 1.0)
    
    def _calculate_relationship_complexity(self, schema: SchemaInfo) -> float:
        """Calculate complexity based on table relationships."""
        total_tables = len(schema.tables)
        if total_tables == 0:
            return 0.0
        
        total_relationships = sum(len(table.foreign_keys) for table in schema.tables)
        return min(total_relationships / (total_tables * 2), 1.0)  # Normalize
    
    def _calculate_size_complexity(self, schema: SchemaInfo) -> float:
        """Calculate complexity based on database size."""
        total_rows = sum(table.row_count for table in schema.tables)
        
        # Size complexity thresholds
        if total_rows < 10000:
            return 0.1
        elif total_rows < 100000:
            return 0.3
        elif total_rows < 1000000:
            return 0.5
        elif total_rows < 10000000:
            return 0.7
        else:
            return 0.9
    
    def _calculate_overall_complexity(self, factors: Dict[str, Any]) -> float:
        """Calculate overall complexity score."""
        weights = {
            "data_types_complexity": 0.3,
            "relationship_complexity": 0.25,
            "size_complexity": 0.2,
            "table_count_factor": 0.15,
            "column_count_factor": 0.1
        }
        
        # Normalize table and column counts
        table_factor = min(factors["table_count"] / 50, 1.0)
        column_factor = min(factors["total_columns"] / 500, 1.0)
        
        complexity = (
            factors["data_types_complexity"] * weights["data_types_complexity"] +
            factors["relationship_complexity"] * weights["relationship_complexity"] +
            factors["size_complexity"] * weights["size_complexity"] +
            table_factor * weights["table_count_factor"] +
            column_factor * weights["column_count_factor"]
        )
        
        return min(complexity, 1.0)
    
    def _get_risk_level_from_complexity(self, complexity: float) -> str:
        """Convert complexity score to risk level."""
        if complexity < RISK_THRESHOLDS["low"]:
            return "low"
        elif complexity < RISK_THRESHOLDS["medium"]:
            return "medium"
        elif complexity < RISK_THRESHOLDS["high"]:
            return "high"
        else:
            return "critical"
    
    def _estimate_migration_duration(self, factors: Dict[str, Any]) -> int:
        """Estimate migration duration in hours."""
        base_hours = 2  # Minimum setup time
        
        # Add time based on complexity factors
        table_hours = factors["table_count"] * 0.5
        column_hours = factors["total_columns"] * 0.1
        complexity_multiplier = 1 + factors["data_types_complexity"] + factors["relationship_complexity"]
        
        estimated_hours = (base_hours + table_hours + column_hours) * complexity_multiplier
        
        return max(int(estimated_hours), 1)
    
    def _generate_migration_steps(self, source_schema: SchemaInfo, target_type: str, mappings: List[DataTypeMapping], config: Dict[str, Any]) -> List[MigrationStep]:
        """Generate detailed migration steps."""
        steps = []
        step_counter = 1
        
        # Step 1: Create target database structure
        for table in source_schema.tables:
            step = MigrationStep(
                step_id=f"step_{step_counter:03d}",
                step_type=MigrationStepType.CREATE_TABLE,
                object_name=table.name,
                sql_script=self._generate_create_table_script(table, target_type, mappings),
                estimated_duration=30,  # 30 seconds per table
                risk_level="low",
                description=f"Create table {table.name}"
            )
            steps.append(step)
            step_counter += 1
        
        # Step 2: Create indexes
        for table in source_schema.tables:
            for index in table.indexes:
                step = MigrationStep(
                    step_id=f"step_{step_counter:03d}",
                    step_type=MigrationStepType.CREATE_INDEX,
                    object_name=f"{table.name}.{index['name']}",
                    sql_script=self._generate_create_index_script(table.name, index, target_type),
                    estimated_duration=60,
                    risk_level="low",
                    description=f"Create index {index['name']} on {table.name}"
                )
                steps.append(step)
                step_counter += 1
        
        # Step 3: Migrate data
        for table in source_schema.tables:
            step = MigrationStep(
                step_id=f"step_{step_counter:03d}",
                step_type=MigrationStepType.MIGRATE_DATA,
                object_name=table.name,
                sql_script=self._generate_data_migration_script(table, target_type, mappings),
                estimated_duration=max(table.row_count // 1000, 60),  # 1 second per 1000 rows, minimum 1 minute
                risk_level=self._assess_data_migration_risk(table),
                description=f"Migrate data for table {table.name}"
            )
            steps.append(step)
            step_counter += 1
        
        # Step 4: Create foreign key constraints
        for table in source_schema.tables:
            for fk in table.foreign_keys:
                step = MigrationStep(
                    step_id=f"step_{step_counter:03d}",
                    step_type=MigrationStepType.ADD_CONSTRAINT,
                    object_name=f"{table.name}.{fk['name']}",
                    sql_script=self._generate_foreign_key_script(table.name, fk, target_type),
                    estimated_duration=30,
                    risk_level="medium",
                    description=f"Add foreign key {fk['name']} to {table.name}",
                    dependencies=[f"step_{i:03d}" for i in range(1, len(source_schema.tables) + 1)]  # Depend on all table creations
                )
                steps.append(step)
                step_counter += 1
        
        return steps
    
    def _get_target_data_type(self, source_type: str, source_db: str, target_db: str) -> str:
        """Map source data type to target database type."""
        # Comprehensive data type mapping
        type_mappings = {
            ("postgresql", "mysql"): {
                "TEXT": "TEXT",
                "VARCHAR": "VARCHAR",
                "INTEGER": "INT",
                "BIGINT": "BIGINT",
                "BOOLEAN": "TINYINT(1)",
                "TIMESTAMP": "TIMESTAMP",
                "DATE": "DATE",
                "DECIMAL": "DECIMAL",
                "JSON": "JSON",
                "UUID": "CHAR(36)"
            },
            ("mysql", "postgresql"): {
                "TEXT": "TEXT",
                "VARCHAR": "VARCHAR",
                "INT": "INTEGER",
                "BIGINT": "BIGINT",
                "TINYINT": "BOOLEAN",
                "TIMESTAMP": "TIMESTAMP",
                "DATE": "DATE",
                "DECIMAL": "DECIMAL",
                "JSON": "JSONB",
                "CHAR": "CHAR"
            },
            ("sqlite", "postgresql"): {
                "TEXT": "TEXT",
                "INTEGER": "INTEGER",
                "REAL": "REAL",
                "BLOB": "BYTEA",
                "NUMERIC": "NUMERIC"
            },
            ("mongodb", "postgresql"): {
                "str": "TEXT",
                "int": "INTEGER",
                "float": "REAL",
                "bool": "BOOLEAN",
                "datetime": "TIMESTAMP",
                "ObjectId": "CHAR(24)",
                "dict": "JSONB",
                "list": "JSONB"
            }
        }
        
        mapping_key = (source_db.lower(), target_db.lower())
        if mapping_key in type_mappings:
            return type_mappings[mapping_key].get(source_type.upper(), "TEXT")
        
        return "TEXT"  # Default fallback
    
    def _requires_conversion(self, source_type: str, target_type: str) -> bool:
        """Check if data type conversion is required."""
        return source_type.upper() != target_type.upper()
    
    def _get_conversion_notes(self, source_type: str, target_type: str) -> str:
        """Get notes about data type conversion."""
        if not self._requires_conversion(source_type, target_type):
            return "Direct mapping, no conversion required"
        
        conversion_notes = {
            ("UUID", "CHAR"): "UUID will be stored as string, ensure proper validation",
            ("JSON", "JSONB"): "JSON will be converted to JSONB for better performance",
            ("TINYINT", "BOOLEAN"): "TINYINT(1) will be converted to BOOLEAN",
            ("BOOLEAN", "TINYINT"): "BOOLEAN will be converted to TINYINT(1)"
        }
        
        key = (source_type.upper(), target_type.upper())
        return conversion_notes.get(key, f"Converting {source_type} to {target_type}")
    
    def _assess_data_loss_risk(self, source_type: str, target_type: str) -> str:
        """Assess risk of data loss during conversion."""
        high_risk_conversions = [
            ("DECIMAL", "FLOAT"),
            ("BIGINT", "INT"),
            ("TEXT", "VARCHAR"),
            ("JSON", "TEXT")
        ]
        
        conversion = (source_type.upper(), target_type.upper())
        if conversion in high_risk_conversions:
            return "high"
        elif self._requires_conversion(source_type, target_type):
            return "medium"
        else:
            return "low"
    
    def _generate_create_table_script(self, table: Any, target_type: str, mappings: List[DataTypeMapping]) -> str:
        """Generate CREATE TABLE script for target database."""
        # This would generate database-specific CREATE TABLE statements
        # Implementation depends on target database syntax
        columns_sql = []
        
        for column in table.columns:
            # Find appropriate mapping
            target_data_type = self._get_target_data_type(column.data_type, "source", target_type)
            
            column_sql = f"{column.name} {target_data_type}"
            
            if not column.is_nullable:
                column_sql += " NOT NULL"
            
            if column.is_primary_key:
                column_sql += " PRIMARY KEY"
            
            if column.default_value:
                column_sql += f" DEFAULT {column.default_value}"
            
            columns_sql.append(column_sql)
        
        return f"CREATE TABLE {table.name} (\n  " + ",\n  ".join(columns_sql) + "\n);"
    
    def _generate_create_index_script(self, table_name: str, index: Dict[str, Any], target_type: str) -> str:
        """Generate CREATE INDEX script."""
        unique_clause = "UNIQUE " if index.get('unique', False) else ""
        columns = ", ".join(index['columns'])
        return f"CREATE {unique_clause}INDEX {index['name']} ON {table_name} ({columns});"
    
    def _generate_data_migration_script(self, table: Any, target_type: str, mappings: List[DataTypeMapping]) -> str:
        """Generate data migration script."""
        columns = ", ".join([col.name for col in table.columns])
        return f"INSERT INTO {table.name} ({columns}) SELECT {columns} FROM source.{table.name};"
    
    def _generate_foreign_key_script(self, table_name: str, fk: Dict[str, Any], target_type: str) -> str:
        """Generate foreign key constraint script."""
        columns = ", ".join(fk['columns'])
        ref_columns = ", ".join(fk['referenced_columns'])
        return f"ALTER TABLE {table_name} ADD CONSTRAINT {fk['name']} FOREIGN KEY ({columns}) REFERENCES {fk['referenced_table']} ({ref_columns});"
    
    def _assess_data_migration_risk(self, table: Any) -> str:
        """Assess risk level for data migration."""
        if table.row_count > 1000000:
            return "high"
        elif table.row_count > 100000:
            return "medium"
        else:
            return "low"
    
    def _calculate_plan_risk_level(self, steps: List[MigrationStep]) -> str:
        """Calculate overall risk level for migration plan."""
        risk_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        
        if not steps:
            return "low"
        
        max_risk = max(risk_scores.get(step.risk_level, 1) for step in steps)
        
        for risk_level, score in risk_scores.items():
            if score == max_risk:
                return risk_level
        
        return "low"
