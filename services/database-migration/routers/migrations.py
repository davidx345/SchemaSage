"""
Migration Operations Router
Migration planning, risk assessment, and execution
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime

from ..models import MigrationPlan, MigrationExecution, RiskAssessment
from ..core.handlers import get_database_handler
from ..core.intelligence import MigrationIntelligence
from ..config import SUPPORTED_DATABASES

router = APIRouter(prefix="/migrations", tags=["migrations"])
logger = logging.getLogger(__name__)

# External dependencies (these would be injected in production)
connections_store: Dict[str, Any] = {}
migration_plans_store: Dict[str, MigrationPlan] = {}
executions_store: Dict[str, MigrationExecution] = {}

# Initialize services
intelligence = MigrationIntelligence()

@router.post("/plan", response_model=MigrationPlan)
async def create_migration_plan(
    source_connection_id: str,
    target_database_type: str,
    migration_config: Optional[Dict[str, Any]] = None
):
    """Create a migration plan."""
    if source_connection_id not in connections_store:
        raise HTTPException(status_code=404, detail="Source connection not found")
    
    if target_database_type.lower() not in SUPPORTED_DATABASES:
        raise HTTPException(status_code=400, detail=f"Unsupported target database type: {target_database_type}")
    
    try:
        # Get source schema
        source_connection = connections_store[source_connection_id]
        source_handler = get_database_handler(source_connection)
        source_handler.connect()
        source_schema = source_handler.extract_schema()
        source_handler.disconnect()
        
        # Generate migration plan using AI
        migration_plan = intelligence.generate_migration_plan(
            source_schema, 
            target_database_type, 
            migration_config or {}
        )
        
        # Generate rollback scripts
        migration_plan = intelligence.generate_rollback_scripts(migration_plan)
        
        # Optimize step order
        migration_plan.steps = intelligence.optimize_migration_order(migration_plan.steps)
        
        # Store migration plan
        migration_plans_store[migration_plan.plan_id] = migration_plan
        
        return migration_plan
    
    except Exception as e:
        logger.error(f"Error creating migration plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans", response_model=List[Dict[str, Any]])
async def list_migration_plans():
    """List all migration plans."""
    plans_list = []
    for plan_id, plan in migration_plans_store.items():
        plans_list.append({
            "plan_id": plan_id,
            "name": plan.name,
            "source_connection_id": plan.source_connection_id,
            "target_connection_id": plan.target_connection_id,
            "status": plan.status,
            "step_count": len(plan.steps),
            "estimated_duration": plan.total_estimated_duration,
            "risk_level": plan.overall_risk_level,
            "created_at": plan.created_at
        })
    return plans_list

@router.get("/plans/{plan_id}", response_model=MigrationPlan)
async def get_migration_plan(plan_id: str):
    """Get a specific migration plan."""
    if plan_id not in migration_plans_store:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    return migration_plans_store[plan_id]

@router.post("/plans/{plan_id}/assess-risk", response_model=RiskAssessment)
async def assess_migration_risk(plan_id: str):
    """Assess risks for a migration plan."""
    if plan_id not in migration_plans_store:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    
    try:
        migration_plan = migration_plans_store[plan_id]
        risk_assessment = intelligence.assess_migration_risks(migration_plan)
        
        return risk_assessment
    
    except Exception as e:
        logger.error(f"Error assessing migration risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute/{plan_id}", response_model=Dict[str, Any])
async def start_migration_execution(plan_id: str, background_tasks: BackgroundTasks):
    """Start migration execution."""
    if plan_id not in migration_plans_store:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    
    try:
        execution_id = str(uuid.uuid4())
        execution = MigrationExecution(
            execution_id=execution_id,
            plan_id=plan_id,
            status="pending",
            started_at=datetime.utcnow()
        )
        
        executions_store[execution_id] = execution
        
        # Start migration in background
        background_tasks.add_task(execute_migration_background, execution_id)
        
        return {
            "execution_id": execution_id,
            "status": "started",
            "message": "Migration execution started in background"
        }
    
    except Exception as e:
        logger.error(f"Error starting migration execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}", response_model=MigrationExecution)
async def get_migration_execution(execution_id: str):
    """Get migration execution status."""
    if execution_id not in executions_store:
        raise HTTPException(status_code=404, detail="Migration execution not found")
    return executions_store[execution_id]

@router.get("/executions", response_model=List[Dict[str, Any]])
async def list_migration_executions():
    """List all migration executions."""
    executions_list = []
    for exec_id, execution in executions_store.items():
        executions_list.append({
            "execution_id": exec_id,
            "plan_id": execution.plan_id,
            "status": execution.status,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "current_step": execution.current_step,
            "completed_steps": len(execution.completed_steps),
            "failed_steps": len(execution.failed_steps)
        })
    return executions_list

@router.post("/analyze/complexity")
async def analyze_migration_complexity(source_connection_id: str, target_database_type: str):
    """Analyze migration complexity."""
    if source_connection_id not in connections_store:
        raise HTTPException(status_code=404, detail="Source connection not found")
    
    try:
        # Get source schema
        source_connection = connections_store[source_connection_id]
        source_handler = get_database_handler(source_connection)
        source_handler.connect()
        source_schema = source_handler.extract_schema()
        source_handler.disconnect()
        
        # Analyze complexity using AI
        complexity_analysis = intelligence.analyze_migration_complexity(source_schema, target_database_type)
        
        return complexity_analysis
    
    except Exception as e:
        logger.error(f"Error analyzing migration complexity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for migration execution
async def execute_migration_background(execution_id: str):
    """Execute migration in background."""
    try:
        execution = executions_store[execution_id]
        execution.status = "running"
        
        # Get migration plan
        migration_plan = migration_plans_store[execution.plan_id]
        
        # Execute each step
        for step in migration_plan.steps:
            execution.current_step = step.step_id
            
            # Simulate step execution (replace with actual execution logic)
            import asyncio
            await asyncio.sleep(1)  # Simulate execution time
            
            # Mark step as completed
            execution.completed_steps.append(step.step_id)
            
            # Log execution
            execution.execution_log.append({
                "step_id": step.step_id,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Step {step.step_id} completed successfully"
            })
        
        # Mark execution as completed
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        
    except Exception as e:
        logger.error(f"Error executing migration {execution_id}: {e}")
        execution = executions_store[execution_id]
        execution.status = "failed"
        execution.execution_log.append({
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Migration execution failed"
        })
