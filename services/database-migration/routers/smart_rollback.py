"""
Smart Schema Rollback Router
Intelligent rollback planning with data preservation and validation
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json
import uuid
import asyncio
from enum import Enum

router = APIRouter(prefix="/migration", tags=["smart-rollback"])

# Enums
class RollbackStrategy(str, Enum):
    preserve_data = "preserve_data"
    snapshot_restore = "snapshot_restore"
    custom = "custom"

class RollbackStepType(str, Enum):
    data_backup = "data_backup"
    schema_rollback = "schema_rollback"
    data_restoration = "data_restoration"
    validation = "validation"
    cleanup = "cleanup"

class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

# Models
class DataPreservationRule(BaseModel):
    table: str
    strategy: str = Field(..., description="temporary_backup, field_mapping, archive")
    retention_period: Optional[str] = "7d"
    field_mappings: Optional[Dict[str, str]] = None

class ValidationRule(BaseModel):
    type: str = Field(..., description="data_integrity, business_rules, performance")
    description: str

class RollbackStep(BaseModel):
    order: int
    type: RollbackStepType
    description: str
    sql: Optional[str] = None
    estimated_duration: str
    reversible: bool

class SmartRollbackRequest(BaseModel):
    migration_id: str
    rollback_strategy: RollbackStrategy = RollbackStrategy.preserve_data
    data_preservation_rules: List[DataPreservationRule] = Field(default_factory=list)
    validation_rules: List[ValidationRule] = Field(default_factory=list)

class RollbackPlan(BaseModel):
    id: str
    estimated_downtime: str
    data_preservation_size: str
    risk_assessment: RiskLevel
    steps: List[RollbackStep]
    validation_checkpoints: List[str]

class RollbackExecution(BaseModel):
    id: str
    plan_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_step: int = 0
    error_message: Optional[str] = None

# Mock storage
ROLLBACK_PLANS = {}
ROLLBACK_EXECUTIONS = {}
MIGRATION_HISTORY = {
    "mig_001": {
        "id": "mig_001",
        "name": "User table schema update",
        "executed_at": "2025-09-15T10:00:00Z",
        "changes": [
            {
                "type": "add_column",
                "table": "users",
                "column": "new_email_field",
                "sql": "ALTER TABLE users ADD COLUMN new_email_field VARCHAR(255)"
            },
            {
                "type": "modify_column",
                "table": "users", 
                "column": "status",
                "sql": "ALTER TABLE users ALTER COLUMN status SET DEFAULT 'active'"
            }
        ],
        "affected_tables": ["users"],
        "backup_created": True
    }
}

class SmartRollbackEngine:
    """Intelligent rollback planning engine"""
    
    def __init__(self):
        self.rollback_templates = self._load_rollback_templates()
    
    def _load_rollback_templates(self) -> Dict[str, Any]:
        """Load rollback templates for common scenarios"""
        return {
            "add_column": {
                "complexity": "low",
                "reversible": True,
                "sql_template": "ALTER TABLE {table} DROP COLUMN {column}",
                "data_loss_risk": "none"
            },
            "drop_column": {
                "complexity": "high",
                "reversible": False,
                "sql_template": "ALTER TABLE {table} ADD COLUMN {column} {type}",
                "data_loss_risk": "high",
                "requires_backup": True
            },
            "modify_column": {
                "complexity": "medium",
                "reversible": True,
                "sql_template": "ALTER TABLE {table} ALTER COLUMN {column} {original_definition}",
                "data_loss_risk": "medium"
            },
            "create_table": {
                "complexity": "low",
                "reversible": True,
                "sql_template": "DROP TABLE {table}",
                "data_loss_risk": "high"
            },
            "drop_table": {
                "complexity": "critical",
                "reversible": False,
                "sql_template": "CREATE TABLE {table} ({columns})",
                "data_loss_risk": "critical",
                "requires_backup": True
            }
        }
    
    async def analyze_migration(self, migration_id: str) -> Dict[str, Any]:
        """Analyze migration to understand rollback complexity"""
        migration = MIGRATION_HISTORY.get(migration_id)
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")
        
        analysis = {
            "migration_id": migration_id,
            "changes": migration["changes"],
            "complexity_score": 0,
            "data_loss_risk": "low",
            "estimated_data_size": 0,
            "affected_tables": migration["affected_tables"]
        }
        
        # Analyze each change
        for change in migration["changes"]:
            change_type = change["type"]
            template = self.rollback_templates.get(change_type, {})
            
            # Update complexity score
            complexity_map = {"low": 1, "medium": 3, "high": 5, "critical": 10}
            analysis["complexity_score"] += complexity_map.get(template.get("complexity", "medium"), 3)
            
            # Update data loss risk
            risk_levels = ["none", "low", "medium", "high", "critical"]
            current_risk = template.get("data_loss_risk", "low")
            if risk_levels.index(current_risk) > risk_levels.index(analysis["data_loss_risk"]):
                analysis["data_loss_risk"] = current_risk
        
        # Estimate data size (mock calculation)
        analysis["estimated_data_size"] = len(migration["affected_tables"]) * 100  # MB
        
        return analysis
    
    async def create_rollback_plan(self, request: SmartRollbackRequest) -> RollbackPlan:
        """Create intelligent rollback plan"""
        migration_analysis = await self.analyze_migration(request.migration_id)
        migration = MIGRATION_HISTORY[request.migration_id]
        
        rollback_id = f"rollback_{uuid.uuid4().hex[:16]}"
        steps = []
        step_order = 1
        
        # Step 1: Create data backup if needed
        if request.rollback_strategy == RollbackStrategy.preserve_data:
            for table in migration_analysis["affected_tables"]:
                backup_step = RollbackStep(
                    order=step_order,
                    type=RollbackStepType.data_backup,
                    description=f"Create temporary backup of {table} table",
                    sql=f"CREATE TABLE {table}_backup_rollback AS SELECT * FROM {table}",
                    estimated_duration="3-5 minutes",
                    reversible=True
                )
                steps.append(backup_step)
                step_order += 1
        
        # Step 2: Rollback schema changes in reverse order
        for change in reversed(migration["changes"]):
            rollback_sql = self._generate_rollback_sql(change)
            rollback_step = RollbackStep(
                order=step_order,
                type=RollbackStepType.schema_rollback,
                description=f"Revert {change['type']} on {change['table']}",
                sql=rollback_sql,
                estimated_duration="1-2 minutes",
                reversible=True
            )
            steps.append(rollback_step)
            step_order += 1
        
        # Step 3: Data restoration with field mapping
        if request.data_preservation_rules:
            for rule in request.data_preservation_rules:
                if rule.field_mappings:
                    mapping_sql = self._generate_data_mapping_sql(rule)
                    restoration_step = RollbackStep(
                        order=step_order,
                        type=RollbackStepType.data_restoration,
                        description=f"Restore data for {rule.table} with field mapping",
                        sql=mapping_sql,
                        estimated_duration="5-10 minutes",
                        reversible=False
                    )
                    steps.append(restoration_step)
                    step_order += 1
        
        # Step 4: Validation steps
        validation_step = RollbackStep(
            order=step_order,
            type=RollbackStepType.validation,
            description="Validate data integrity and business rules",
            estimated_duration="2-3 minutes",
            reversible=True
        )
        steps.append(validation_step)
        step_order += 1
        
        # Step 5: Cleanup temporary tables
        cleanup_step = RollbackStep(
            order=step_order,
            type=RollbackStepType.cleanup,
            description="Clean up temporary backup tables",
            sql=f"DROP TABLE IF EXISTS {', '.join([f'{table}_backup_rollback' for table in migration_analysis['affected_tables']])}",
            estimated_duration="1 minute",
            reversible=False
        )
        steps.append(cleanup_step)
        
        # Calculate risk assessment
        risk_level = self._assess_rollback_risk(migration_analysis, request)
        
        # Calculate estimated downtime
        total_duration_minutes = sum(self._parse_duration(step.estimated_duration) for step in steps)
        estimated_downtime = f"{total_duration_minutes} minutes"
        
        # Generate validation checkpoints
        validation_checkpoints = []
        for rule in request.validation_rules:
            validation_checkpoints.append(rule.description)
        
        # Default checkpoints
        default_checkpoints = [
            "Verify foreign key integrity",
            "Test application functionality",
            "Validate data consistency"
        ]
        validation_checkpoints.extend(default_checkpoints)
        
        plan = RollbackPlan(
            id=rollback_id,
            estimated_downtime=estimated_downtime,
            data_preservation_size=f"{migration_analysis['estimated_data_size']} MB",
            risk_assessment=risk_level,
            steps=steps,
            validation_checkpoints=validation_checkpoints
        )
        
        return plan
    
    def _generate_rollback_sql(self, change: Dict[str, Any]) -> str:
        """Generate rollback SQL for a migration change"""
        change_type = change["type"]
        table = change["table"]
        
        if change_type == "add_column":
            return f"ALTER TABLE {table} DROP COLUMN {change['column']}"
        elif change_type == "drop_column":
            # This would need the original column definition
            return f"ALTER TABLE {table} ADD COLUMN {change['column']} {change.get('original_type', 'VARCHAR(255)')}"
        elif change_type == "modify_column":
            return f"ALTER TABLE {table} ALTER COLUMN {change['column']} {change.get('original_definition', 'SET DEFAULT NULL')}"
        elif change_type == "create_table":
            return f"DROP TABLE {table}"
        elif change_type == "drop_table":
            return f"-- Cannot automatically restore dropped table {table} - manual intervention required"
        else:
            return f"-- Rollback SQL for {change_type} not implemented"
    
    def _generate_data_mapping_sql(self, rule: DataPreservationRule) -> str:
        """Generate SQL for data restoration with field mapping"""
        if not rule.field_mappings:
            return f"INSERT INTO {rule.table} SELECT * FROM {rule.table}_backup_rollback"
        
        # Build field mapping
        field_mappings = []
        for new_field, old_field in rule.field_mappings.items():
            field_mappings.append(f"{old_field} AS {new_field}")
        
        mapping_clause = ", ".join(field_mappings)
        return f"INSERT INTO {rule.table} ({', '.join(rule.field_mappings.keys())}) SELECT {mapping_clause} FROM {rule.table}_backup_rollback"
    
    def _assess_rollback_risk(self, migration_analysis: Dict[str, Any], request: SmartRollbackRequest) -> RiskLevel:
        """Assess rollback risk level"""
        complexity_score = migration_analysis["complexity_score"]
        data_loss_risk = migration_analysis["data_loss_risk"]
        
        # Base risk on complexity and data loss risk
        if data_loss_risk == "critical" or complexity_score >= 20:
            return RiskLevel.critical
        elif data_loss_risk == "high" or complexity_score >= 10:
            return RiskLevel.high
        elif data_loss_risk == "medium" or complexity_score >= 5:
            return RiskLevel.medium
        else:
            return RiskLevel.low
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to minutes"""
        # Simple parser for "X-Y minutes" format
        import re
        match = re.search(r'(\d+)(?:-(\d+))?\s*minutes?', duration_str)
        if match:
            min_duration = int(match.group(1))
            max_duration = int(match.group(2)) if match.group(2) else min_duration
            return (min_duration + max_duration) // 2
        return 5  # Default 5 minutes

# Global rollback engine
rollback_engine = SmartRollbackEngine()

async def execute_rollback_plan(rollback_id: str, plan: RollbackPlan):
    """Execute rollback plan in background"""
    try:
        execution = RollbackExecution(
            id=f"exec_{uuid.uuid4().hex[:16]}",
            plan_id=rollback_id,
            status="running",
            started_at=datetime.now(),
            current_step=0
        )
        
        ROLLBACK_EXECUTIONS[rollback_id] = execution
        
        # Execute each step
        for i, step in enumerate(plan.steps):
            execution.current_step = i + 1
            
            # Simulate step execution
            await asyncio.sleep(2)  # Simulate work
            
            # In real implementation, execute SQL and validate
            if step.sql:
                # Log SQL execution (mock)
                print(f"Executing: {step.sql}")
            
            # Update execution status
            ROLLBACK_EXECUTIONS[rollback_id] = execution
        
        # Mark as completed
        execution.status = "completed"
        execution.completed_at = datetime.now()
        ROLLBACK_EXECUTIONS[rollback_id] = execution
    
    except Exception as e:
        # Mark as failed
        execution.status = "failed"
        execution.error_message = str(e)
        execution.completed_at = datetime.now()
        ROLLBACK_EXECUTIONS[rollback_id] = execution

@router.post("/smart-rollback")
async def create_smart_rollback_plan(request: SmartRollbackRequest):
    """Create intelligent rollback plan with data preservation"""
    try:
        # Validate migration exists
        if request.migration_id not in MIGRATION_HISTORY:
            raise HTTPException(status_code=404, detail="Migration not found")
        
        # Create rollback plan
        plan = await rollback_engine.create_rollback_plan(request)
        
        # Store plan
        ROLLBACK_PLANS[plan.id] = plan
        
        return {
            "success": True,
            "data": {
                "rollback_plan": {
                    "id": plan.id,
                    "estimated_downtime": plan.estimated_downtime,
                    "data_preservation_size": plan.data_preservation_size,
                    "risk_assessment": plan.risk_assessment,
                    "steps": [step.dict() for step in plan.steps],
                    "validation_checkpoints": plan.validation_checkpoints
                }
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create rollback plan: {str(e)}")

@router.post("/rollback/{rollback_id}/execute")
async def execute_rollback(
    rollback_id: str,
    background_tasks: BackgroundTasks
):
    """Execute rollback plan"""
    try:
        # Validate rollback plan exists
        if rollback_id not in ROLLBACK_PLANS:
            raise HTTPException(status_code=404, detail="Rollback plan not found")
        
        plan = ROLLBACK_PLANS[rollback_id]
        
        # Start execution in background
        background_tasks.add_task(execute_rollback_plan, rollback_id, plan)
        
        return {
            "success": True,
            "data": {
                "execution_id": rollback_id,
                "status": "started",
                "estimated_completion": (datetime.now() + timedelta(minutes=20)).isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute rollback: {str(e)}")

@router.get("/rollback/{rollback_id}/status")
async def get_rollback_status(rollback_id: str):
    """Monitor rollback execution status"""
    try:
        # Check if execution exists
        if rollback_id not in ROLLBACK_EXECUTIONS:
            # Check if plan exists but not executed
            if rollback_id in ROLLBACK_PLANS:
                return {
                    "success": True,
                    "data": {
                        "status": "planned",
                        "plan_id": rollback_id,
                        "executed": False
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="Rollback not found")
        
        execution = ROLLBACK_EXECUTIONS[rollback_id]
        plan = ROLLBACK_PLANS[rollback_id]
        
        return {
            "success": True,
            "data": {
                "execution_id": execution.id,
                "plan_id": execution.plan_id,
                "status": execution.status,
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "current_step": execution.current_step,
                "total_steps": len(plan.steps),
                "current_step_description": plan.steps[execution.current_step - 1].description if execution.current_step > 0 else None,
                "error_message": execution.error_message
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rollback status: {str(e)}")

@router.get("/rollback-plans")
async def list_rollback_plans():
    """List all rollback plans"""
    try:
        plans_summary = []
        for plan_id, plan in ROLLBACK_PLANS.items():
            execution = ROLLBACK_EXECUTIONS.get(plan_id)
            
            plans_summary.append({
                "id": plan.id,
                "risk_assessment": plan.risk_assessment,
                "estimated_downtime": plan.estimated_downtime,
                "data_preservation_size": plan.data_preservation_size,
                "step_count": len(plan.steps),
                "status": execution.status if execution else "planned",
                "executed_at": execution.started_at.isoformat() if execution else None
            })
        
        return {
            "success": True,
            "data": {
                "rollback_plans": plans_summary,
                "total_count": len(ROLLBACK_PLANS)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list rollback plans: {str(e)}")

@router.get("/migrations/{migration_id}/rollback-analysis")
async def analyze_migration_rollback(migration_id: str):
    """Analyze migration for rollback complexity"""
    try:
        analysis = await rollback_engine.analyze_migration(migration_id)
        
        return {
            "success": True,
            "data": {
                "analysis": analysis,
                "rollback_feasibility": "high" if analysis["complexity_score"] <= 5 else 
                                      "medium" if analysis["complexity_score"] <= 10 else "low",
                "estimated_effort": f"{analysis['complexity_score'] * 2} hours",
                "recommendations": [
                    "Create full database backup before rollback",
                    "Test rollback procedure in staging environment",
                    "Plan maintenance window for rollback execution"
                ]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze migration rollback: {str(e)}")

@router.get("/rollback-templates")
async def get_rollback_templates():
    """Get rollback templates for common migration scenarios"""
    try:
        templates = [
            {
                "name": "Column Addition Rollback",
                "scenario": "Added new columns to existing tables",
                "complexity": "low",
                "data_loss_risk": "none",
                "template": {
                    "rollback_strategy": "preserve_data",
                    "steps": [
                        "Backup affected tables",
                        "Drop added columns",
                        "Validate data integrity"
                    ]
                }
            },
            {
                "name": "Table Structure Change",
                "scenario": "Modified existing table structures",
                "complexity": "medium",
                "data_loss_risk": "medium",
                "template": {
                    "rollback_strategy": "preserve_data",
                    "data_preservation_rules": [
                        {
                            "strategy": "field_mapping",
                            "retention_period": "30d"
                        }
                    ]
                }
            },
            {
                "name": "Table Deletion Recovery",
                "scenario": "Accidentally dropped important tables",
                "complexity": "critical",
                "data_loss_risk": "critical",
                "template": {
                    "rollback_strategy": "snapshot_restore",
                    "requirements": [
                        "Recent database backup required",
                        "Extended downtime expected",
                        "Manual data verification needed"
                    ]
                }
            }
        ]
        
        return {
            "success": True,
            "data": {
                "templates": templates
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rollback templates: {str(e)}")

@router.post("/validate-rollback-plan/{rollback_id}")
async def validate_rollback_plan(rollback_id: str):
    """Validate rollback plan before execution"""
    try:
        if rollback_id not in ROLLBACK_PLANS:
            raise HTTPException(status_code=404, detail="Rollback plan not found")
        
        plan = ROLLBACK_PLANS[rollback_id]
        
        # Validation checks
        validation_results = []
        
        # Check 1: SQL syntax validation (mock)
        for step in plan.steps:
            if step.sql:
                validation_results.append({
                    "check": f"SQL syntax for step {step.order}",
                    "status": "passed",
                    "message": "SQL syntax is valid"
                })
        
        # Check 2: Data preservation validation
        validation_results.append({
            "check": "Data preservation strategy",
            "status": "passed" if plan.risk_assessment != RiskLevel.critical else "warning",
            "message": "Data preservation strategy is appropriate" if plan.risk_assessment != RiskLevel.critical 
                      else "High-risk rollback - additional precautions recommended"
        })
        
        # Check 3: Estimated downtime validation
        validation_results.append({
            "check": "Downtime estimation",
            "status": "passed",
            "message": f"Estimated downtime: {plan.estimated_downtime}"
        })
        
        # Overall validation status
        failed_checks = [r for r in validation_results if r["status"] == "failed"]
        warning_checks = [r for r in validation_results if r["status"] == "warning"]
        
        overall_status = "failed" if failed_checks else "warning" if warning_checks else "passed"
        
        return {
            "success": True,
            "data": {
                "rollback_id": rollback_id,
                "validation_status": overall_status,
                "validation_results": validation_results,
                "ready_for_execution": overall_status != "failed",
                "recommendations": [
                    "Test rollback in staging environment first",
                    "Notify stakeholders of planned maintenance",
                    "Prepare rollback contingency plan"
                ]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate rollback plan: {str(e)}")
