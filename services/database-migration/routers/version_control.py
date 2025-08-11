"""
Version Control & CI/CD Router
Git repository integration, schema branches, and CI/CD pipeline management
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging

from ..models.version_control import GitRepository, SchemaBranch
from ..models.cicd import CIPipeline
from ..core.version_control import SchemaVersionControl
from ..core.cicd import PipelineOrchestrator

router = APIRouter(tags=["version-control", "cicd"])
logger = logging.getLogger(__name__)

# External dependencies (these would be injected in production)
workspaces_store: Dict[str, Any] = {}
git_repositories_store: Dict[str, GitRepository] = {}
pipelines_store: Dict[str, CIPipeline] = {}

# Initialize services (would be injected in production)
version_control = SchemaVersionControl()
pipeline_orchestrator = PipelineOrchestrator()

# Version Control Integration
@router.post("/workspaces/{workspace_id}/git-repositories", response_model=Dict[str, Any])
async def connect_git_repository(workspace_id: str, repo_data: Dict[str, Any]):
    """Connect a Git repository for version control."""
    if workspace_id not in workspaces_store:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        git_repo = GitRepository(
            workspace_id=workspace_id,
            provider=repo_data["provider"],
            repository_url=repo_data["repository_url"],
            repository_name=repo_data["repository_name"],
            owner=repo_data["owner"],
            access_token=repo_data.get("access_token"),
            default_branch=repo_data.get("default_branch", "main")
        )
        
        git_repositories_store[git_repo.repo_id] = git_repo
        
        return {
            "repo_id": git_repo.repo_id,
            "message": "Git repository connected successfully",
            "repository": git_repo.model_dump()
        }
    
    except Exception as e:
        logger.error(f"Error connecting git repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/git-repositories/{repo_id}/branches", response_model=SchemaBranch)
async def create_schema_branch(repo_id: str, branch_data: Dict[str, Any]):
    """Create a new schema branch."""
    if repo_id not in git_repositories_store:
        raise HTTPException(status_code=404, detail="Git repository not found")
    
    try:
        repo = git_repositories_store[repo_id]
        schema_branch = await version_control.create_schema_branch(
            "/tmp/repo",  # Would be actual repo path
            branch_data["branch_name"],
            branch_data.get("base_branch", repo.default_branch)
        )
        
        return schema_branch
    
    except Exception as e:
        logger.error(f"Error creating schema branch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CI/CD Pipeline Management
@router.post("/workspaces/{workspace_id}/pipelines", response_model=Dict[str, Any])
async def create_cicd_pipeline(workspace_id: str, pipeline_data: Dict[str, Any]):
    """Create a CI/CD pipeline."""
    if workspace_id not in workspaces_store:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        pipeline = CIPipeline(
            workspace_id=workspace_id,
            name=pipeline_data["name"],
            platform=pipeline_data["platform"],
            repository_id=pipeline_data["repository_id"],
            trigger_events=pipeline_data.get("trigger_events", ["push", "pull_request"]),
            target_branches=pipeline_data.get("target_branches", ["main"]),
            created_by=pipeline_data["created_by"]
        )
        
        pipelines_store[pipeline.pipeline_id] = pipeline
        
        return {
            "pipeline_id": pipeline.pipeline_id,
            "message": "CI/CD pipeline created successfully",
            "pipeline": pipeline.model_dump()
        }
    
    except Exception as e:
        logger.error(f"Error creating pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pipelines/{pipeline_id}/execute", response_model=Dict[str, Any])
async def execute_pipeline(pipeline_id: str, background_tasks: BackgroundTasks, trigger_data: Dict[str, Any]):
    """Execute a CI/CD pipeline."""
    if pipeline_id not in pipelines_store:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    try:
        pipeline = pipelines_store[pipeline_id]
        
        # Start pipeline execution in background
        background_tasks.add_task(execute_pipeline_background, pipeline_id, trigger_data)
        
        return {
            "message": "Pipeline execution started",
            "pipeline_id": pipeline_id
        }
    
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for pipeline execution
async def execute_pipeline_background(pipeline_id: str, trigger_data: Dict[str, Any]):
    """Execute CI/CD pipeline in background."""
    try:
        pipeline = pipelines_store[pipeline_id]
        execution = await pipeline_orchestrator.execute_pipeline(pipeline, trigger_data)
        
        # Store execution results (would be in database in production)
        logger.info(f"Pipeline {pipeline_id} execution completed with status: {execution.status}")
        
    except Exception as e:
        logger.error(f"Error executing pipeline {pipeline_id}: {e}")
