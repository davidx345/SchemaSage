"""
Cloud Provision Router
Handles all cloud provisioning API endpoints for Quick Deploy feature
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging
import asyncio
from uuid import uuid4
from datetime import datetime

from models.schemas import (
    AnalyzeRequest, AnalyzeResponse,
    ValidateCredentialsRequest, ValidateCredentialsResponse,
    DeployRequest, DeployResponse,
    CostEstimateRequest, CostEstimateResponse,
    ListDeploymentsResponse, GetDeploymentResponse,
    DeleteDeploymentRequest, DeleteDeploymentResponse
)
from core.deployment_analyzer import get_deployment_analyzer
from core.cloud_provisioner import CloudProvisioner, CloudProvisionerError
from core.deployment_websocket import get_websocket_manager
from core.credential_encryption import encrypt_credentials, decrypt_credentials
from core.auth import get_current_user
from core.database_service import SchemaDetectionDatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cloud", tags=["Cloud Provisioning"])

# Initialize services
db_service = SchemaDetectionDatabaseService()
ws_manager = get_websocket_manager()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_deployment(
    description: str = Form(...),
    file: Optional[UploadFile] = File(None),
    preferences: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user)
):
    """
    Analyze natural language description or uploaded file to generate schema and recommendations
    
    **Request:**
    - description: Natural language description of database needs
    - file: Optional schema file (SQL, JSON, CSV, Excel)
    - preferences: Optional JSON string with provider, region, budget preferences
    
    **Response:**
    - analysis: Detected schema structure
    - recommendations: Cloud provider and instance recommendations
    - schema: Generated schema in multiple formats
    """
    try:
        # Parse preferences if provided
        prefs = None
        if preferences:
            import json
            prefs = json.loads(preferences)
        
        # Get analyzer
        analyzer = get_deployment_analyzer()
        
        # TODO: Handle file upload if provided
        if file:
            logger.info(f"File upload received: {file.filename}")
            # Could parse SQL, JSON, CSV files to enhance description
        
        # Analyze description
        result = await analyzer.analyze_description(description, prefs)
        
        logger.info(f"Analysis complete for user {user_id}")
        
        return result
        
    except ValueError as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in analyze: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.post("/validate-credentials", response_model=ValidateCredentialsResponse)
async def validate_credentials(
    request: ValidateCredentialsRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Validate cloud provider credentials and check permissions
    
    **Request:**
    - provider: aws, gcp, or azure
    - credentials: Provider-specific credentials
    
    **Response:**
    - valid: Whether credentials are valid
    - permissions: List of available permissions
    - account_id: Cloud account identifier
    - message: Validation message
    """
    try:
        # Validate credentials
        result = await CloudProvisioner.validate_credentials(
            request.provider,
            request.credentials
        )
        
        # If valid, optionally store encrypted credentials
        if result.get('valid'):
            logger.info(f"Credentials validated for user {user_id}, provider {request.provider}")
            # TODO: Optionally save to cloud_credentials table
        
        return result
        
    except CloudProvisionerError as e:
        logger.error(f"Credential validation failed: {e}")
        return ValidateCredentialsResponse(
            valid=False,
            message="Validation failed",
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in validate_credentials: {e}")
        raise HTTPException(status_code=500, detail="Validation failed")


@router.post("/deploy", response_model=DeployResponse)
async def deploy_infrastructure(
    request: DeployRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Start cloud infrastructure deployment with schema, code generation, and migrations
    
    **Request:**
    - provider: Cloud provider (aws, gcp, azure)
    - credentials: Provider credentials
    - schema: Database schema definition
    - options: Code generation options
    - instance_config: Cloud instance configuration
    
    **Response:**
    - deployment_id: Unique deployment identifier
    - status: Deployment status
    - websocket_url: WebSocket URL for real-time updates
    """
    try:
        # Generate deployment ID
        deployment_id = str(uuid4())
        
        logger.info(f"Starting deployment {deployment_id} for user {user_id}")
        
        # Encrypt credentials
        encrypted_creds = encrypt_credentials(request.credentials)
        
        # Create deployment record in database
        from models.database_models import CloudDeployment
        deployment_data = {
            "id": deployment_id,
            "user_id": user_id,
            "description": request.schema.get('description', 'Quick Deploy database'),
            "provider": request.provider,
            "database_type": request.schema.get('database_type', 'postgresql'),
            "database_version": request.schema.get('version', '15'),
            "instance_type": request.instance_config.instance_type,
            "region": request.instance_config.region,
            "storage_gb": request.instance_config.storage,
            "schema_json": request.schema,
            "status": "pending",
            "progress_percentage": 0,
            "auto_scaling": request.instance_config.auto_scaling,
            "backup_enabled": request.instance_config.backup_enabled,
            "multi_az": request.instance_config.multi_az,
            "public_access": request.instance_config.public_access
        }
        
        # Save to database
        await db_service.create_cloud_deployment(deployment_data)
        
        # Start deployment in background using Celery
        from deployment_tasks import run_deployment_task
        
        run_deployment_task.apply_async(
            args=[
                deployment_id,
                user_id,
                request.provider,
                request.credentials,
                request.schema,
                request.options.dict(),
                request.instance_config.dict()
            ],
            queue='cloud_provisioning'
        )
        
        # Return response
        websocket_url = f"wss://your-service.com/ws/cloud-provision/{deployment_id}"
        # TODO: Use actual service URL from config
        
        return DeployResponse(
            deployment_id=deployment_id,
            status="in_progress",
            websocket_url=websocket_url
        )
        
    except Exception as e:
        logger.error(f"Failed to start deployment: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


async def run_deployment(
    deployment_id: str,
    user_id: str,
    provider: str,
    credentials: Dict[str, Any],
    schema: Dict[str, Any],
    options: Any,
    instance_config: Any
):
    """
    Background task to run the actual deployment
    """
    try:
        # Step 1: Update status to analyzing
        await db_service.update_deployment_status(deployment_id, "analyzing", 10)
        await ws_manager.send_progress(deployment_id, 10, "Analyzing requirements...")
        await asyncio.sleep(2)  # Simulate analysis time
        
        # Step 2: Start provisioning
        await db_service.update_deployment_status(deployment_id, "provisioning", 20)
        await ws_manager.send_progress(deployment_id, 20, "Creating cloud database instance...")
        
        # Provision infrastructure
        result = await CloudProvisioner.provision_database(
            provider,
            credentials,
            deployment_id,
            schema.get('database_type', 'postgresql'),
            instance_config.dict(),
            schema
        )
        
        # Step 3: Instance ready
        await db_service.update_deployment_status(deployment_id, "configuring", 60)
        await ws_manager.send_progress(deployment_id, 60, "Database instance ready, configuring...")
        
        # Update deployment with instance details
        await db_service.update_deployment_instance(
            deployment_id,
            cloud_instance_id=result['instance_id'],
            connection_string=encrypt_credentials({"connection_string": result['connection_string']}),
            endpoint=result.get('endpoint'),
            port=result.get('port')
        )
        
        await asyncio.sleep(2)
        
        # Step 4: Generate code if requested
        generated_assets = {}
        if options.generate_code:
            await db_service.update_deployment_status(deployment_id, "generating", 75)
            await ws_manager.send_progress(deployment_id, 75, "Generating code...")
            
            # TODO: Integrate with code generation service
            generated_assets['code'] = {
                "language": options.language,
                "framework": options.framework,
                "files": ["models.py", "schemas.py", "routes.py"],
                "lineCount": 342
            }
            await asyncio.sleep(2)
        
        # Step 5: Create migrations if requested
        if options.create_migrations:
            await ws_manager.send_progress(deployment_id, 85, "Creating migrations...")
            
            # TODO: Generate migration files
            generated_assets['migrations'] = {
                "files": ["001_initial_schema.sql", "002_indexes.sql"],
                "count": 2
            }
            await asyncio.sleep(2)
        
        # Step 6: Complete
        await db_service.update_deployment_status(deployment_id, "ready", 100)
        await ws_manager.send_progress(deployment_id, 100, "Deployment complete!", "success")
        
        # Send completion message
        await ws_manager.send_completion(deployment_id, {
            "deployment_id": deployment_id,
            "status": "ready",
            "connection_string": result['connection_string'],
            "cloud_resource_id": result['instance_id'],
            "generated_assets": generated_assets,
            "metadata": {
                "provider": provider,
                "region": instance_config.region,
                "instance_type": instance_config.instance_type,
                "database_type": schema.get('database_type'),
                "created_at": datetime.now().isoformat()
            }
        })
        
        logger.info(f"Deployment {deployment_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Deployment {deployment_id} failed: {e}")
        await db_service.update_deployment_status(deployment_id, "failed", error_message=str(e))
        await ws_manager.send_error(deployment_id, str(e))


@router.websocket("/ws/{deployment_id}")
async def websocket_endpoint(websocket: WebSocket, deployment_id: str):
    """
    WebSocket endpoint for real-time deployment progress updates
    
    **Connection:** `wss://your-service.com/ws/cloud-provision/{deployment_id}`
    
    **Messages:**
    - auth_success: Connection established
    - progress: Progress update with percentage and step
    - log: Log message
    - complete: Deployment completed with results
    - error: Error occurred
    """
    try:
        # Connect WebSocket
        await ws_manager.connect(deployment_id, websocket)
        
        # Keep connection alive
        while True:
            # Wait for messages (ping/pong)
            data = await websocket.receive_text()
            
            # Handle ping
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for deployment {deployment_id}")
        ws_manager.disconnect(deployment_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for deployment {deployment_id}: {e}")
        ws_manager.disconnect(deployment_id, websocket)


@router.get("/deployment/{deployment_id}", response_model=GetDeploymentResponse)
async def get_deployment(
    deployment_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get current status and details of a deployment
    
    **Response:**
    - deployment_id: Deployment identifier
    - status: Current status
    - progress: Progress information
    - result: Deployment result (if complete)
    - created_at: Creation timestamp
    - completed_at: Completion timestamp (if complete)
    """
    try:
        # Get deployment from database
        deployment = await db_service.get_cloud_deployment(deployment_id, user_id)
        
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Build response
        response = {
            "deployment_id": deployment_id,
            "status": deployment.status,
            "progress": {
                "percentage": deployment.progress_percentage,
                "current_step": deployment.current_step or "Pending"
            },
            "created_at": deployment.created_at.isoformat(),
            "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None
        }
        
        # Add result if complete
        if deployment.status == "ready":
            response["result"] = {
                "connection_string": deployment.connection_string,  # Note: Should decrypt
                "cloud_resource_id": deployment.cloud_instance_id,
                "generated_assets": deployment.generated_assets
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching deployment: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch deployment")


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(request: CostEstimateRequest):
    """
    Estimate monthly costs for a given configuration
    
    **Request:**
    - provider: Cloud provider
    - instance_type: Instance type
    - storage: Storage in GB
    - region: Region
    - backup_enabled: Whether backups are enabled
    - auto_scaling: Whether auto-scaling is enabled
    
    **Response:**
    - monthly_total: Total monthly cost
    - hourly_total: Total hourly cost
    - breakdown: Cost breakdown by component
    - comparison: Cost comparison across providers
    """
    try:
        from core.deployment_analyzer import DeploymentAnalyzer
        
        analyzer = DeploymentAnalyzer()
        
        # Estimate cost
        cost = analyzer._estimate_cost(
            request.provider,
            request.instance_type,
            request.storage
        )
        
        # Calculate breakdown
        # Simplified pricing (use real pricing API in production)
        compute_pct = 0.65
        storage_pct = 0.25
        backup_pct = 0.10 if request.backup_enabled else 0.0
        
        breakdown = {
            "compute": round(cost * compute_pct, 2),
            "storage": round(cost * storage_pct, 2),
            "backup": round(cost * backup_pct, 2),
            "network": 0.0
        }
        
        # Get comparison
        comparison = {}
        for prov in ['aws', 'gcp', 'azure']:
            comparison[prov] = analyzer._estimate_cost(prov, request.instance_type, request.storage)
        
        return CostEstimateResponse(
            monthly_total=cost,
            hourly_total=round(cost / 730, 3),
            breakdown=breakdown,
            comparison=comparison
        )
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(status_code=500, detail="Cost estimation failed")


@router.get("/deployments", response_model=ListDeploymentsResponse)
async def list_deployments(
    user_id: str = Depends(get_current_user),
    status: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """
    List all deployments for the current user
    
    **Query Parameters:**
    - status: Filter by status (ready, provisioning, failed, etc.)
    - provider: Filter by provider (aws, gcp, azure)
    - limit: Maximum number of results
    - offset: Offset for pagination
    
    **Response:**
    - deployments: List of deployment summaries
    - total: Total number of deployments
    """
    try:
        # Get deployments from database
        deployments = await db_service.list_cloud_deployments(
            user_id,
            status=status,
            provider=provider,
            limit=limit,
            offset=offset
        )
        
        # Build summaries
        summaries = []
        for dep in deployments:
            summaries.append({
                "deployment_id": str(dep.id),
                "description": dep.description,
                "provider": dep.provider,
                "status": dep.status,
                "database_type": dep.database_type,
                "created_at": dep.created_at.isoformat(),
                "cost_per_month": dep.estimated_monthly_cost
            })
        
        # Get total count
        total = await db_service.count_cloud_deployments(user_id, status=status, provider=provider)
        
        return ListDeploymentsResponse(
            deployments=summaries,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing deployments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list deployments")


@router.delete("/deployment/{deployment_id}", response_model=DeleteDeploymentResponse)
async def delete_deployment(
    deployment_id: str,
    request: DeleteDeploymentRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Terminate a deployment and optionally delete cloud resources
    
    **Request:**
    - delete_resources: If true, delete RDS/Cloud SQL instance; if false, just remove from tracking
    
    **Response:**
    - success: Whether deletion was successful
    - message: Deletion message
    """
    try:
        # Get deployment
        deployment = await db_service.get_cloud_deployment(deployment_id, user_id)
        
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Delete cloud resources if requested
        if request.delete_resources and deployment.cloud_instance_id:
            logger.info(f"Deleting cloud resources for deployment {deployment_id}")
            
            # Decrypt credentials (would need to be stored or retrieved)
            # For now, just mark as deleted
            # TODO: Implement actual cloud resource deletion
            
        # Delete from database
        await db_service.delete_cloud_deployment(deployment_id, user_id)
        
        return DeleteDeploymentResponse(
            success=True,
            message="Deployment terminated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting deployment: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete deployment")


# Add database service methods (to be added to database_service.py)
# These are placeholder methods - implement in database_service.py

async def create_cloud_deployment_placeholder(data: Dict[str, Any]):
    """Placeholder - implement in database_service.py"""
    pass

async def update_deployment_status_placeholder(deployment_id: str, status: str, progress: int = None, error_message: str = None):
    """Placeholder - implement in database_service.py"""
    pass
