"""
Migration Planner Core Logic.
Generates comprehensive migration plans for cross-database migrations.
"""
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

from models.universal_migration_models import (
    MigrationPlanData, SourceAnalysis, TargetAnalysis, MigrationPlan,
    MigrationStep, DatabaseType, RiskLevel, MigrationType
)

class MigrationPlanner:
    """
    Generates migration plans for cross-database migrations.
    """
    
    def create_plan(self, source_url: str, target_url: str, migration_type: MigrationType, options: Dict[str, Any]) -> MigrationPlanData:
        """
        Creates a comprehensive migration plan.
        """
        migration_id = f"mig_{str(uuid4())[:8]}"
        
        # Parse database types from connection strings
        source_type = self._parse_db_type(source_url)
        target_type = self._parse_db_type(target_url)
        
        # Analyze source database
        source_analysis = self._analyze_source(source_url, source_type)
        
        # Analyze target database
        target_analysis = self._analyze_target(target_url, target_type, source_analysis)
        
        # Generate migration plan
        migration_plan = self._generate_plan(
            source_type,
            target_type,
            migration_type,
            source_analysis,
            target_analysis,
            options
        )
        
        # Determine if cross-database migration
        cross_database = source_type != target_type
        migration_type_str = f"{source_type.upper()} → {target_type.upper()}" if cross_database else f"{source_type.upper()} version upgrade"
        
        return MigrationPlanData(
            migration_id=migration_id,
            source_analysis=source_analysis,
            target_analysis=target_analysis,
            migration_plan=migration_plan,
            cross_database_migration=cross_database,
            migration_type=migration_type_str
        )
    
    def _parse_db_type(self, connection_string: str) -> str:
        """Parses database type from connection string."""
        if connection_string.startswith("postgresql://"):
            return "postgresql"
        elif connection_string.startswith("mysql://"):
            return "mysql"
        elif connection_string.startswith("mongodb://"):
            return "mongodb"
        elif connection_string.startswith("mssql://") or "sqlserver://" in connection_string:
            return "mssql"
        elif connection_string.startswith("oracle://"):
            return "oracle"
        else:
            return "unknown"
    
    def _analyze_source(self, source_url: str, db_type: str) -> SourceAnalysis:
        """Analyzes source database."""
        # Simulated source analysis
        if db_type == "postgresql":
            return SourceAnalysis(
                database_type="PostgreSQL 14.5",
                total_tables=87,
                total_records=2456789,
                total_size_gb=12.4,
                schemas=["public", "sales", "inventory"],
                relationships=[
                    {"from": "orders", "to": "users", "type": "many-to-one"},
                    {"from": "order_items", "to": "orders", "type": "many-to-one"},
                    {"from": "order_items", "to": "products", "type": "many-to-one"}
                ]
            )
        elif db_type == "mysql":
            return SourceAnalysis(
                database_type="MySQL 8.0",
                total_tables=65,
                total_records=1850000,
                total_size_gb=9.2,
                schemas=["main", "analytics"],
                relationships=[
                    {"from": "transactions", "to": "accounts", "type": "many-to-one"}
                ]
            )
        else:
            return SourceAnalysis(
                database_type=f"{db_type.upper()} (version unknown)",
                total_tables=50,
                total_records=1000000,
                total_size_gb=8.0,
                schemas=["default"],
                relationships=[]
            )
    
    def _analyze_target(
        self,
        target_url: str,
        db_type: str,
        source_analysis: SourceAnalysis
    ) -> TargetAnalysis:
        """Analyzes target database compatibility."""
        # Simulated target analysis
        if db_type == "mongodb":
            compatibility = 75  # PostgreSQL → MongoDB has moderate compatibility
            transformations = [
                "Convert relational tables to embedded documents",
                "Flatten many-to-many relationships",
                "Convert JOIN queries to $lookup aggregations"
            ]
        elif db_type == "postgresql":
            compatibility = 95  # PostgreSQL → PostgreSQL high compatibility
            transformations = [
                "Update sequences for AUTO_INCREMENT",
                "Migrate stored procedures to PL/pgSQL"
            ]
        else:
            compatibility = 80
            transformations = ["Schema mapping required", "Data type conversion needed"]
        
        return TargetAnalysis(
            database_type=f"{db_type.upper()} 6.0" if db_type == "mongodb" else f"{db_type.upper()} latest",
            available_space_gb=500.0,
            compatibility_score=compatibility,
            required_transformations=transformations
        )
    
    def _generate_plan(
        self,
        source_type: str,
        target_type: str,
        migration_type: MigrationType,
        source_analysis: SourceAnalysis,
        target_analysis: TargetAnalysis,
        options: Dict[str, Any]
    ) -> MigrationPlan:
        """Generates detailed migration plan."""
        steps = []
        step_num = 1
        
        # Step 1: Pre-migration validation
        steps.append(MigrationStep(
            step_number=step_num,
            description="Validate source and target connections",
            estimated_duration="5 minutes",
            dependencies=[],
            risk_level=RiskLevel.LOW
        ))
        step_num += 1
        
        # Step 2: Schema analysis
        if migration_type in [MigrationType.SCHEMA_ONLY, MigrationType.SCHEMA_AND_DATA]:
            steps.append(MigrationStep(
                step_number=step_num,
                description="Analyze and map source schema to target",
                estimated_duration="15 minutes",
                dependencies=[1],
                risk_level=RiskLevel.MEDIUM
            ))
            step_num += 1
            
            steps.append(MigrationStep(
                step_number=step_num,
                description="Create target schema structure",
                estimated_duration="10 minutes",
                dependencies=[2],
                risk_level=RiskLevel.MEDIUM
            ))
            step_num += 1
        
        # Step 3: Data migration
        if migration_type in [MigrationType.DATA_ONLY, MigrationType.SCHEMA_AND_DATA]:
            steps.append(MigrationStep(
                step_number=step_num,
                description="Migrate reference/lookup tables",
                estimated_duration="20 minutes",
                dependencies=[3] if migration_type == MigrationType.SCHEMA_AND_DATA else [],
                risk_level=RiskLevel.LOW
            ))
            step_num += 1
            
            steps.append(MigrationStep(
                step_number=step_num,
                description="Migrate transactional data",
                estimated_duration="3-5 hours",
                dependencies=[step_num - 1],
                risk_level=RiskLevel.HIGH
            ))
            step_num += 1
        
        # Step 4: Index creation
        steps.append(MigrationStep(
            step_number=step_num,
            description="Create indexes and constraints",
            estimated_duration="30 minutes",
            dependencies=[step_num - 1],
            risk_level=RiskLevel.MEDIUM
        ))
        step_num += 1
        
        # Step 5: Verification
        steps.append(MigrationStep(
            step_number=step_num,
            description="Verify data integrity and completeness",
            estimated_duration="20 minutes",
            dependencies=[step_num - 1],
            risk_level=RiskLevel.LOW
        ))
        
        # Identify compatibility issues
        compatibility_issues = []
        if source_type != target_type:
            compatibility_issues.append(f"Cross-database migration: {source_type} → {target_type}")
            compatibility_issues.append("Schema transformation required")
            
        if source_type == "postgresql" and target_type == "mongodb":
            compatibility_issues.append("Relational to document model conversion")
            compatibility_issues.append("Foreign key constraints not supported in MongoDB")
        
        # Data transformations
        data_transformations = []
        if target_type == "mongodb":
            data_transformations.append({
                "from": "orders + order_items (JOIN)",
                "to": "orders collection with embedded items array"
            })
            data_transformations.append({
                "from": "users.id (INTEGER)",
                "to": "_id (ObjectId)"
            })
        
        return MigrationPlan(
            estimated_duration="4-6 hours",
            total_steps=len(steps),
            steps=steps,
            compatibility_issues=compatibility_issues,
            data_transformations=data_transformations,
            rollback_available=True
        )
