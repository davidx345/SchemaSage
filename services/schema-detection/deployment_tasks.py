"""
Celery Tasks for Cloud Deployment
Handles long-running cloud provisioning operations
"""
import os
import asyncio
import httpx
import logging
from typing import Dict, Any
from celery_app import celery_app

logger = logging.getLogger(__name__)

# Service URLs
CODE_GENERATION_SERVICE_URL = os.getenv(
    "CODE_GENERATION_SERVICE_URL",
    "http://localhost:8003"
)
DATABASE_MIGRATION_SERVICE_URL = os.getenv(
    "DATABASE_MIGRATION_SERVICE_URL",
    "http://localhost:8002"
)


@celery_app.task(bind=True, name="deployment_tasks.run_deployment_task")
def run_deployment_task(
    self,
    deployment_id: str,
    user_id: str,
    provider: str,
    credentials: Dict[str, Any],
    schema: Dict[str, Any],
    options: Dict[str, Any],
    instance_config: Dict[str, Any]
):
    """
    Celery task to run cloud deployment in background
    
    Args:
        self: Celery task instance
        deployment_id: Unique deployment ID
        user_id: User ID
        provider: Cloud provider (aws, gcp, azure)
        credentials: Cloud credentials
        schema: Database schema
        options: Generation options
        instance_config: Instance configuration
    """
    try:
        # Run async deployment in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _run_deployment_async(
                deployment_id,
                user_id,
                provider,
                credentials,
                schema,
                options,
                instance_config
            )
        )
        
        loop.close()
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"Deployment task failed: {e}")
        # Update deployment status to failed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_handle_deployment_error(deployment_id, str(e)))
        loop.close()
        
        raise


async def _run_deployment_async(
    deployment_id: str,
    user_id: str,
    provider: str,
    credentials: Dict[str, Any],
    schema: Dict[str, Any],
    options: Dict[str, Any],
    instance_config: Dict[str, Any]
):
    """Async implementation of deployment"""
    from core.cloud_provisioner import CloudProvisioner
    from core.deployment_websocket import get_websocket_manager
    from core.database_service import SchemaDetectionDatabaseService
    from core.credential_encryption import encrypt_credentials
    from datetime import datetime
    import time
    
    ws_manager = get_websocket_manager()
    db_service = SchemaDetectionDatabaseService()
    await db_service.initialize()
    
    try:
        # Step 1: Update status to analyzing
        await db_service.update_deployment_status(deployment_id, "analyzing", 10)
        await ws_manager.send_progress(deployment_id, 10, "Analyzing requirements...")
        await asyncio.sleep(2)
        
        # Step 2: Start provisioning
        await db_service.update_deployment_status(deployment_id, "provisioning", 20)
        await ws_manager.send_progress(deployment_id, 20, "Creating cloud database instance...")
        await ws_manager.send_log(deployment_id, "info", f"Provisioning {schema.get('database_type')} on {provider.upper()}", "provisioning")
        
        # Provision infrastructure
        result = await CloudProvisioner.provision_database(
            provider,
            credentials,
            deployment_id,
            schema.get('database_type', 'postgresql'),
            instance_config,
            schema
        )
        
        # Step 3: Instance ready
        await db_service.update_deployment_status(deployment_id, "configuring", 60)
        await ws_manager.send_progress(deployment_id, 60, "Database instance ready, configuring...")
        await ws_manager.send_log(deployment_id, "success", f"Instance {result['instance_id']} is ready", "provisioning")
        
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
        if options.get('generate_code', True):
            await db_service.update_deployment_status(deployment_id, "generating", 75)
            await ws_manager.send_progress(deployment_id, 75, "Generating code...")
            await ws_manager.send_log(deployment_id, "info", f"Generating {options.get('language', 'typescript')} code...", "code_generation")
            
            # Call code generation service
            code_result = await _generate_code(schema, options)
            generated_assets['code'] = code_result
            
            await asyncio.sleep(2)
        
        # Step 5: Create migrations if requested
        if options.get('create_migrations', True):
            await ws_manager.send_progress(deployment_id, 85, "Creating migrations...")
            await ws_manager.send_log(deployment_id, "info", "Generating database migrations...", "migrations")
            
            # Call migration service
            migration_result = await _generate_migrations(schema, result.get('connection_string'))
            generated_assets['migrations'] = migration_result
            
            await asyncio.sleep(2)
        
        # Step 6: Complete
        await db_service.update_deployment_status(deployment_id, "ready", 100)
        await ws_manager.send_progress(deployment_id, 100, "Deployment complete!", "success")
        await ws_manager.send_log(deployment_id, "success", "All deployment tasks completed successfully!", "complete")
        
        # Send completion message
        await ws_manager.send_completion(deployment_id, {
            "deployment_id": deployment_id,
            "status": "ready",
            "connection_string": result['connection_string'],
            "cloud_resource_id": result['instance_id'],
            "generated_assets": generated_assets,
            "metadata": {
                "provider": provider,
                "region": instance_config.get('region'),
                "instance_type": instance_config.get('instance_type'),
                "database_type": schema.get('database_type'),
                "created_at": datetime.now().isoformat()
            }
        })
        
        logger.info(f"Deployment {deployment_id} completed successfully")
        
        return {
            "deployment_id": deployment_id,
            "status": "ready",
            "connection_string": result['connection_string'],
            "instance_id": result['instance_id']
        }
        
    except Exception as e:
        logger.error(f"Deployment {deployment_id} failed: {e}")
        await db_service.update_deployment_status(deployment_id, "failed", error_message=str(e))
        await ws_manager.send_error(deployment_id, str(e))
        raise
    finally:
        await db_service.close()


async def _handle_deployment_error(deployment_id: str, error: str):
    """Handle deployment error"""
    from core.deployment_websocket import get_websocket_manager
    from core.database_service import SchemaDetectionDatabaseService
    
    ws_manager = get_websocket_manager()
    db_service = SchemaDetectionDatabaseService()
    
    try:
        await db_service.initialize()
        await db_service.update_deployment_status(deployment_id, "failed", error_message=error)
        await ws_manager.send_error(deployment_id, error)
    finally:
        await db_service.close()


async def _generate_code(schema: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call code generation service to generate code
    
    Args:
        schema: Database schema
        options: Generation options
        
    Returns:
        Dict with generated code information
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{CODE_GENERATION_SERVICE_URL}/api/generation/generate-code",
                json={
                    "schema": schema,
                    "language": options.get('language', 'typescript'),
                    "framework": options.get('framework', 'fastapi'),
                    "include_tests": True,
                    "include_docs": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "language": options.get('language', 'typescript'),
                    "framework": options.get('framework', 'fastapi'),
                    "files": result.get('files', []),
                    "lineCount": sum(f.get('lineCount', 0) for f in result.get('files', []))
                }
            else:
                logger.error(f"Code generation failed: {response.text}")
                return {
                    "language": options.get('language', 'typescript'),
                    "error": "Code generation service unavailable"
                }
                
    except Exception as e:
        logger.error(f"Failed to call code generation service: {e}")
        return {
            "language": options.get('language', 'typescript'),
            "error": str(e)
        }


async def _generate_migrations(schema: Dict[str, Any], connection_string: str) -> Dict[str, Any]:
    """
    Call database migration service to generate migrations
    
    Args:
        schema: Database schema
        connection_string: Database connection string
        
    Returns:
        Dict with migration files
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{DATABASE_MIGRATION_SERVICE_URL}/api/migrations/generate",
                json={
                    "schema": schema,
                    "connection_string": connection_string,
                    "migration_type": "alembic",
                    "auto_apply": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "files": result.get('migrations', []),
                    "count": len(result.get('migrations', []))
                }
            else:
                logger.error(f"Migration generation failed: {response.text}")
                return {
                    "error": "Migration service unavailable"
                }
                
    except Exception as e:
        logger.error(f"Failed to call migration service: {e}")
        return {
            "error": str(e)
        }


@celery_app.task(bind=True, name="deployment_tasks.generate_code_task")
def generate_code_task(self, schema: Dict[str, Any], options: Dict[str, Any]):
    """Standalone code generation task"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_generate_code(schema, options))
        return result
    finally:
        loop.close()


@celery_app.task(bind=True, name="deployment_tasks.generate_migrations_task")
def generate_migrations_task(self, schema: Dict[str, Any], connection_string: str):
    """Standalone migration generation task"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_generate_migrations(schema, connection_string))
        return result
    finally:
        loop.close()
