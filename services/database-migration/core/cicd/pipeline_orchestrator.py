"""
Pipeline Orchestrator Module
Orchestrates CI/CD pipeline execution with stage and step management.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any

from .migration_test_runner import MigrationTestRunner
from ...models.cicd import CIPipeline, PipelineExecution, JobExecution, PipelineStatus

class PipelineOrchestrator:
    """Orchestrates CI/CD pipeline execution."""
    
    def __init__(self):
        self.github_integration = None
        self.jenkins_integration = None
        self.test_runner = MigrationTestRunner()
    
    async def execute_pipeline(self, pipeline: CIPipeline, trigger_context: Dict[str, Any]) -> PipelineExecution:
        """Execute a complete CI/CD pipeline."""
        execution = PipelineExecution(
            pipeline_id=pipeline.pipeline_id,
            workspace_id=pipeline.workspace_id,
            trigger_type=trigger_context.get("type", "manual"),
            trigger_user=trigger_context.get("user_id"),
            commit_sha=trigger_context.get("commit_sha", "unknown"),
            branch_name=trigger_context.get("branch", "main")
        )
        
        try:
            execution.status = PipelineStatus.RUNNING
            
            # Execute pipeline stages
            for stage in pipeline.stages:
                job_execution = await self._execute_stage(stage, execution)
                execution.job_executions.append(job_execution.job_id)
                
                if job_execution.status == PipelineStatus.FAILED:
                    execution.status = PipelineStatus.FAILED
                    break
            
            if execution.status == PipelineStatus.RUNNING:
                execution.status = PipelineStatus.SUCCESS
            
        except Exception as e:
            execution.status = PipelineStatus.FAILED
            execution.errors.append(str(e))
        
        finally:
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
        
        return execution
    
    async def _execute_stage(self, stage: Dict[str, Any], execution: PipelineExecution) -> JobExecution:
        """Execute a pipeline stage."""
        job_execution = JobExecution(
            execution_id=execution.execution_id,
            job_name=stage.get("name", "unknown"),
            job_type=stage.get("type", "generic"),
            environment=stage.get("environment", "test"),
            configuration=stage
        )
        
        job_execution.status = PipelineStatus.RUNNING
        job_execution.started_at = datetime.utcnow()
        
        try:
            # Execute stage steps
            for step in stage.get("steps", []):
                await self._execute_step(step, job_execution)
            
            job_execution.status = PipelineStatus.SUCCESS
            
        except Exception as e:
            job_execution.status = PipelineStatus.FAILED
            job_execution.error_logs.append(str(e))
        
        finally:
            job_execution.completed_at = datetime.utcnow()
            job_execution.duration_seconds = (job_execution.completed_at - job_execution.started_at).total_seconds()
        
        return job_execution
    
    async def _execute_step(self, step: Dict[str, Any], job_execution: JobExecution):
        """Execute a single pipeline step."""
        step_name = step.get("name", "unknown")
        step_command = step.get("run", "")
        
        job_execution.output_logs.append(f"Executing step: {step_name}")
        
        if step_command:
            # Execute shell command
            result = await self._run_command(step_command)
            job_execution.output_logs.extend(result["stdout"])
            if result["stderr"]:
                job_execution.error_logs.extend(result["stderr"])
            
            if result["returncode"] != 0:
                raise Exception(f"Step failed with exit code {result['returncode']}")
    
    async def _run_command(self, command: str) -> Dict[str, Any]:
        """Run shell command asynchronously."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode().splitlines() if stdout else [],
                "stderr": stderr.decode().splitlines() if stderr else []
            }
        except Exception as e:
            return {
                "returncode": 1,
                "stdout": [],
                "stderr": [str(e)]
            }
