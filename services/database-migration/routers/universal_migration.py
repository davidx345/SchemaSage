"""
Universal Database Migration API Routes
Handles universal database connections and cross-database migrations
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
import asyncio
import uuid

from shared.utils.connection_parser import ConnectionURLParser
from shared.utils.database_manager import connection_manager
from shared.utils.migration_engine import migration_engine, MigrationType, MigrationStatus

# Import Celery tasks and result tracking
from celery.result import AsyncResult
from tasks import extract_schema_task, migrate_data_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["Universal Database Operations"])

# WebSocket connections for real-time updates
active_websockets = {}

@router.get("/supported")
async def get_supported_databases():
    """Get list of supported database types with connection URL formats"""
    try:
        logger.info("Getting supported database types and URL formats")
        
        supported_schemes = ConnectionURLParser.get_supported_schemes()
        
        return {
            "supported_databases": supported_schemes,
            "total_supported": len(supported_schemes),
            "connection_url_formats": {
                "postgresql": {
                    "format": "postgresql://username:password@host:port/database",
                    "options": "?ssl=require&application_name=SchemaSage",
                    "examples": [
                        "postgresql://user:pass@localhost:5432/mydb",
                        "postgresql://user:pass@host:5432/db?ssl=require"
                    ]
                },
                "mysql": {
                    "format": "mysql://username:password@host:port/database",
                    "options": "?charset=utf8mb4&ssl=preferred",
                    "examples": [
                        "mysql://user:pass@localhost:3306/mydb",
                        "mysql://user:pass@host:3306/db?ssl=required"
                    ]
                },
                "mongodb": {
                    "format": "mongodb://username:password@host:port/database",
                    "options": "?authSource=admin&replicaSet=rs0",
                    "examples": [
                        "mongodb://user:pass@localhost:27017/mydb",
                        "mongodb://user:pass@host:27017/db?authSource=admin"
                    ]
                },
                "sqlite": {
                    "format": "sqlite:///path/to/database.db",
                    "options": "Special case - file-based database",
                    "examples": [
                        "sqlite:///path/to/database.db",
                        "sqlite://:memory:"
                    ]
                },
                "redis": {
                    "format": "redis://username:password@host:port/database",
                    "options": "?ssl=true",
                    "examples": [
                        "redis://localhost:6379/0",
                        "redis://user:pass@host:6379/0?ssl=true"
                    ]
                }
            },
            "url_validation_rules": [
                "URLs must include the database type as the scheme",
                "Username and password are required for network databases",
                "Host and port are required for network databases",
                "Database name is required (except for Redis where it's the number)",
                "SQLite only requires the file path",
                "Special characters in passwords should be URL-encoded"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting supported databases: {e}")
        raise HTTPException(status_code=500, detail="Failed to get supported databases")

@router.post("/test-connection-url")
async def test_database_connection(request: Dict[str, Any]):
    """Test database connection using connection URL"""
    try:
        connection_url = request.get("connection_url")
        db_type = request.get("type", "").lower()
        
        if not connection_url:
            return {
                "success": False,
                "error": {
                    "message": "connection_url is required",
                    "code": "INVALID_REQUEST",
                    "details": {
                        "reason": "Missing required field: connection_url"
                    }
                }
            }
        
        logger.info(f"Testing database connection: {ConnectionURLParser.mask_sensitive_data(connection_url)}")
        
        # Validate URL format first
        is_valid, error_message = ConnectionURLParser.validate_connection_url(connection_url)
        if not is_valid:
            return {
                "success": False,
                "error": {
                    "message": f"Invalid connection URL: {error_message}",
                    "code": "INVALID_URL",
                    "details": {
                        "reason": error_message,
                        "database_type": db_type or "unknown"
                    }
                }
            }
        
        # Test connection
        result = await connection_manager.test_connection(connection_url)
        
        # Transform to spec format
        if result['status'] == 'success':
            return {
                "success": True,
                "message": "Connection successful",
                "connection_info": {
                    "database_name": result.get('connection_details', {}).get('database', 'unknown'),
                    "database_type": result.get('database_type', 'unknown'),
                    "database_version": result.get('server_info', {}).get('version', 'unknown'),
                    "server_info": {
                        "host": result.get('connection_details', {}).get('host', 'unknown'),
                        "port": result.get('connection_details', {}).get('port', 0)
                    },
                    "connection_time_ms": result.get('connection_time_ms', 0),
                    "tested_at": result.get('tested_at', datetime.now().isoformat())
                }
            }
        else:
            # Map error types to codes
            error_str = str(result.get('error', 'Unknown error')).lower()
            if 'timeout' in error_str:
                error_code = "TIMEOUT"
            elif 'auth' in error_str or 'password' in error_str or 'permission' in error_str:
                error_code = "AUTH_FAILED"
            elif 'ssl' in error_str or 'tls' in error_str:
                error_code = "SSL_ERROR"
            elif 'unsupported' in error_str:
                error_code = "UNSUPPORTED_DB"
            else:
                error_code = "CONNECTION_FAILED"
            
            return {
                "success": False,
                "error": {
                    "message": result.get('error', 'Connection failed'),
                    "code": error_code,
                    "details": {
                        "reason": result.get('error', 'Unknown error'),
                        "database_type": result.get('database_type', 'unknown')
                    }
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        return {
            "success": False,
            "error": {
                "message": f"Connection test failed: {str(e)}",
                "code": "CONNECTION_FAILED",
                "details": {
                    "reason": str(e),
                    "database_type": db_type or "unknown"
                }
            }
        }

@router.get("/test/history")
async def get_connection_test_history(limit: int = 20):
    """Get history of database connection tests"""
    try:
        logger.info(f"Getting connection test history (limit: {limit})")
        
        # Get all connections health data
        health_data = await connection_manager.get_all_connections_health()
        
        # Convert to history format
        history = []
        for conn_id, status in health_data.get('connections', {}).items():
            history.append({
                'connection_id': conn_id,
                'status': status.get('status'),
                'database_type': status.get('database_type'),
                'tested_at': status.get('last_check'),
                'response_time_ms': status.get('response_time_ms'),
                'error': status.get('error')
            })
        
        # Sort by test date and limit results
        history.sort(key=lambda x: x.get('tested_at', ''), reverse=True)
        history = history[:limit]
        
        return {
            'history': history,
            'summary': health_data.get('summary', {}),
            'metadata': {
                'total_tests': len(health_data.get('connections', {})),
                'returned_count': len(history),
                'generated_at': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting connection test history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connection test history")

@router.post("/import-from-url")
async def import_database_schema(request: Dict[str, Any]):
    """
    Import schema from database using connection URL (async with Celery)
    Returns immediately with a task_id for polling progress
    """
    try:
        connection_url = request.get("connection_url")
        db_type = request.get("type", "").lower()
        import_options = request.get("options", {})
        
        if not connection_url:
            return {
                "success": False,
                "error": {
                    "message": "connection_url is required",
                    "code": "INVALID_REQUEST",
                    "details": {
                        "reason": "Missing required field: connection_url"
                    }
                }
            }
        
        logger.info(f"Starting async schema import: {ConnectionURLParser.mask_sensitive_data(connection_url)}")
        
        # Validate connection URL format (quick validation)
        is_valid, error_message = ConnectionURLParser.validate_connection_url(connection_url)
        if not is_valid:
            return {
                "success": False,
                "error": {
                    "message": f"Invalid connection URL: {error_message}",
                    "code": "INVALID_URL",
                    "details": {
                        "reason": error_message,
                        "database_type": db_type or "unknown"
                    }
                }
            }
        
        # Enqueue Celery task for background processing
        task = extract_schema_task.apply_async(
            args=[connection_url, import_options],
            queue='schema_extraction'
        )
        
        logger.info(f"Schema extraction task queued with ID: {task.id}")
        
        # Return task ID immediately for polling
        return {
            "success": True,
            "task_id": task.id,
            "status": "pending",
            "message": "Schema extraction started in background",
            "status_url": f"/database/import-status/{task.id}",
            "polling_interval_ms": 2000  # Suggest polling every 2 seconds
        }
        
    except Exception as e:
        logger.error(f"Error queueing schema import: {e}", exc_info=True)
        return {
            "success": False,
            "error": {
                "message": f"Failed to start schema import: {str(e)}",
                "code": "IMPORT_FAILED",
                "details": {
                    "reason": str(e),
                    "database_type": db_type or "unknown"
                }
            }
        }

# Store for import jobs (in real implementation, use database)
import_jobs = {}

async def process_schema_import_task(job_id: str, connection_url: str, options: Dict[str, Any]):
    """Background task to process schema import"""
    try:
        logger.info(f"Processing schema import job {job_id}")
        
        # Update job status
        import_jobs[job_id] = {
            'job_id': job_id,
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'progress': {
                'percentage': 10,
                'current_step': 'connecting_to_database',
                'tables_processed': 0,
                'total_tables': 0
            }
        }
        
        # Simulate import process
        steps = [
            ('connecting_to_database', 20),
            ('discovering_schema', 40),
            ('analyzing_tables', 60),
            ('extracting_metadata', 80),
            ('finalizing_import', 100)
        ]
        
        for step_name, progress in steps:
            # Update progress
            import_jobs[job_id]['progress'].update({
                'percentage': progress,
                'current_step': step_name
            })
            
            # Notify WebSocket clients
            await notify_websocket_clients('import_progress', {
                'job_id': job_id,
                'progress': import_jobs[job_id]['progress']
            })
            
            # Simulate work
            await asyncio.sleep(2)
        
        # Complete the job
        db_params = ConnectionURLParser.parse_connection_url(connection_url)
        schema_info = await migration_engine._get_database_schema(db_params)
        
        import_jobs[job_id].update({
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'progress': {
                'percentage': 100,
                'current_step': 'completed',
                'tables_processed': len(schema_info.get('tables', [])),
                'total_tables': len(schema_info.get('tables', []))
            },
            'result': {
                'schema_info': schema_info,
                'import_summary': {
                    'tables_imported': len(schema_info.get('tables', [])),
                    'views_imported': len(schema_info.get('views', [])),
                    'functions_imported': len(schema_info.get('functions', [])),
                    'total_columns': sum(len(table.get('columns', [])) for table in schema_info.get('tables', []))
                }
            }
        })
        
        await notify_websocket_clients('import_completed', {
            'job_id': job_id,
            'status': 'completed'
        })
        
        logger.info(f"Schema import job {job_id} completed successfully")
        
    except Exception as e:
        # Mark job as failed
        import_jobs[job_id].update({
            'status': 'failed',
            'failed_at': datetime.now().isoformat(),
            'error': str(e)
        })
        
        await notify_websocket_clients('import_failed', {
            'job_id': job_id,
            'error': str(e)
        })
        
        logger.error(f"Schema import job {job_id} failed: {e}")

@router.get("/import-status/{task_id}")
async def get_import_task_status(task_id: str):
    """
    Get status of schema import Celery task
    Polls the Celery result backend for task progress
    """
    try:
        logger.info(f"Checking status for task: {task_id}")
        
        # Get task result from Celery
        task_result = AsyncResult(task_id)
        
        # Map Celery states to our response format
        if task_result.state == 'PENDING':
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is queued and waiting to start",
                "progress": {
                    "percentage": 0,
                    "message": "Waiting in queue"
                }
            }
        
        elif task_result.state == 'STARTED':
            return {
                "task_id": task_id,
                "status": "running",
                "message": "Schema extraction is in progress",
                "progress": {
                    "percentage": 5,
                    "message": "Task started"
                }
            }
        
        elif task_result.state == 'PROGRESS':
            # Custom progress state with detailed info
            progress_info = task_result.info or {}
            return {
                "task_id": task_id,
                "status": "running",
                "message": progress_info.get('message', 'Extracting schema'),
                "progress": {
                    "percentage": progress_info.get('percentage', 0),
                    "current": progress_info.get('current', 0),
                    "total": progress_info.get('total', 100),
                    "message": progress_info.get('message', ''),
                    "timestamp": progress_info.get('timestamp')
                }
            }
        
        elif task_result.state == 'SUCCESS':
            # Task completed successfully
            result = task_result.result
            
            if result.get('success'):
                schema = result.get('schema', {})
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "message": "Schema extraction completed successfully",
                    "progress": {
                        "percentage": 100,
                        "message": "Completed"
                    },
                    "result": {
                        "success": True,
                        "schema": schema
                    }
                }
            else:
                # Task completed but with error result
                error = result.get('error', {})
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "message": error.get('message', 'Schema extraction failed'),
                    "error": error
                }
        
        elif task_result.state == 'FAILURE':
            # Task failed with exception
            error_info = str(task_result.info) if task_result.info else 'Unknown error'
            logger.error(f"Task {task_id} failed: {error_info}")
            
            return {
                "task_id": task_id,
                "status": "failed",
                "message": "Schema extraction failed",
                "error": {
                    "message": f"Task execution failed: {error_info}",
                    "code": "EXTRACTION_FAILED",
                    "details": {
                        "reason": error_info
                    }
                }
            }
        
        elif task_result.state == 'RETRY':
            return {
                "task_id": task_id,
                "status": "retrying",
                "message": "Task is being retried after failure",
                "progress": {
                    "percentage": 0,
                    "message": "Retrying..."
                }
            }
        
        elif task_result.state == 'REVOKED':
            return {
                "task_id": task_id,
                "status": "cancelled",
                "message": "Task was cancelled"
            }
        
        else:
            # Unknown state
            return {
                "task_id": task_id,
                "status": "unknown",
                "message": f"Task in unknown state: {task_result.state}",
                "celery_state": task_result.state
            }
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )

@router.post("/import/{task_id}/cancel")
async def cancel_import_task(task_id: str):
    """Cancel schema import Celery task"""
    try:
        logger.info(f"Cancelling task: {task_id}")
        
        # Get task result
        task_result = AsyncResult(task_id)
        
        # Check if task exists and is cancellable
        if task_result.state in ['PENDING', 'STARTED', 'PROGRESS', 'RETRY']:
            # Revoke the task
            task_result.revoke(terminate=True, signal='SIGTERM')
            
            logger.info(f"Task {task_id} cancelled successfully")
            
            return {
                'task_id': task_id,
                'status': 'cancelled',
                'message': 'Schema extraction task cancelled successfully'
            }
        
        elif task_result.state in ['SUCCESS', 'FAILURE']:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task that has already completed (state: {task_result.state})"
            )
        
        elif task_result.state == 'REVOKED':
            return {
                'task_id': task_id,
                'status': 'cancelled',
                'message': 'Task was already cancelled'
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task in state: {task_result.state}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")

# Migration API endpoints
@router.post("/create-migration-plan")
async def create_migration_plan(request: Dict[str, Any]):
    """Create a migration plan between two databases"""
    try:
        source_url = request.get("source_url")
        target_url = request.get("target_url")
        migration_type = request.get("migration_type", MigrationType.SCHEMA_AND_DATA)
        options = request.get("options", {})
        
        if not source_url or not target_url:
            raise HTTPException(status_code=400, detail="source_url and target_url are required")
        
        logger.info(f"Creating migration plan from {ConnectionURLParser.mask_sensitive_data(source_url)} to {ConnectionURLParser.mask_sensitive_data(target_url)}")
        
        # Create migration plan
        migration_plan = await migration_engine.create_migration_plan(
            source_url=source_url,
            target_url=target_url,
            migration_type=MigrationType(migration_type),
            options=options
        )
        
        return migration_plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating migration plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create migration plan: {str(e)}")

@router.post("/execute-migration")
async def execute_migration(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Execute a migration plan"""
    try:
        migration_id = request.get("migration_id")
        execute_options = request.get("options", {})
        
        if not migration_id:
            raise HTTPException(status_code=400, detail="migration_id is required")
        
        # Check if migration plan exists
        if migration_id not in migration_engine.migration_plans:
            raise HTTPException(status_code=404, detail="Migration plan not found")
        
        logger.info(f"Executing migration {migration_id}")
        
        # Create execution record
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        execution_record = {
            'execution_id': execution_id,
            'migration_id': migration_id,
            'status': MigrationStatus.RUNNING,
            'started_at': datetime.now().isoformat(),
            'options': execute_options,
            'progress': {
                'current_step': 1,
                'total_steps': len(migration_engine.migration_plans[migration_id]['migration_plan']['steps']),
                'percentage': 0,
                'current_operation': 'Initializing migration',
                'records_processed': 0,
                'total_records': 0
            }
        }
        
        migration_engine.migration_executions[execution_id] = execution_record
        
        # Start background execution
        background_tasks.add_task(
            execute_migration_task,
            execution_id,
            migration_id,
            execute_options
        )
        
        return {
            'execution_id': execution_id,
            'status': MigrationStatus.RUNNING,
            'message': 'Migration execution started',
            'status_endpoint': f'/api/database/migrations/{execution_id}/status'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing migration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute migration: {str(e)}")

async def execute_migration_task(execution_id: str, migration_id: str, options: Dict[str, Any]):
    """Background task to execute migration"""
    try:
        logger.info(f"Executing migration task {execution_id}")
        
        execution = migration_engine.migration_executions[execution_id]
        migration_plan = migration_engine.migration_plans[migration_id]
        steps = migration_plan['migration_plan']['steps']
        
        total_steps = len(steps)
        
        for i, step in enumerate(steps, 1):
            # Update progress
            execution['progress'].update({
                'current_step': i,
                'percentage': int((i / total_steps) * 100),
                'current_operation': step['description']
            })
            
            # Notify WebSocket clients
            await notify_websocket_clients('migration_progress', {
                'execution_id': execution_id,
                'progress': execution['progress']
            })
            
            # Simulate step execution
            step_duration = step.get('estimated_time_minutes', 2) * 10  # Convert to seconds for demo
            await asyncio.sleep(min(step_duration, 5))  # Cap at 5 seconds for demo
        
        # Complete migration
        execution.update({
            'status': MigrationStatus.COMPLETED,
            'completed_at': datetime.now().isoformat(),
            'progress': {
                'current_step': total_steps,
                'total_steps': total_steps,
                'percentage': 100,
                'current_operation': 'Migration completed successfully',
                'records_processed': 50000,  # Mock data
                'total_records': 50000
            }
        })
        
        await notify_websocket_clients('migration_completed', {
            'execution_id': execution_id,
            'status': MigrationStatus.COMPLETED
        })
        
        logger.info(f"Migration execution {execution_id} completed successfully")
        
    except Exception as e:
        # Mark execution as failed
        migration_engine.migration_executions[execution_id].update({
            'status': MigrationStatus.FAILED,
            'failed_at': datetime.now().isoformat(),
            'error': str(e)
        })
        
        await notify_websocket_clients('migration_failed', {
            'execution_id': execution_id,
            'error': str(e)
        })
        
        logger.error(f"Migration execution {execution_id} failed: {e}")

@router.get("/migration-status/{execution_id}")
async def get_migration_status(execution_id: str):
    """Get status of migration execution"""
    try:
        if execution_id not in migration_engine.migration_executions:
            raise HTTPException(status_code=404, detail="Migration execution not found")
        
        execution = migration_engine.migration_executions[execution_id]
        
        # Add runtime information if running
        if execution['status'] == MigrationStatus.RUNNING:
            started_at = datetime.fromisoformat(execution['started_at'])
            elapsed_seconds = (datetime.now() - started_at).total_seconds()
            
            progress_percentage = execution['progress']['percentage']
            if progress_percentage > 0:
                estimated_total_seconds = elapsed_seconds / (progress_percentage / 100)
                remaining_seconds = max(0, estimated_total_seconds - elapsed_seconds)
            else:
                remaining_seconds = 0
            
            execution['runtime_info'] = {
                'elapsed_seconds': round(elapsed_seconds, 1),
                'estimated_remaining_seconds': round(remaining_seconds, 1)
            }
        
        return execution
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting migration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get migration status")

# WebSocket endpoint for real-time updates
@router.websocket("/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket endpoint for real-time database operation monitoring"""
    client_id = str(uuid.uuid4())
    
    try:
        await websocket.accept()
        active_websockets[client_id] = websocket
        
        logger.info(f"WebSocket client {client_id} connected")
        
        # Send initial connection message
        await websocket.send_text(json.dumps({
            'type': 'connection_established',
            'client_id': client_id,
            'message': 'Connected to SchemaSage monitoring'
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages or keep alive
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                message = json.loads(data)
                
                # Handle different message types
                if message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    }))
                
                elif message.get('type') == 'subscribe':
                    # Handle subscription to specific events
                    await websocket.send_text(json.dumps({
                        'type': 'subscribed',
                        'events': message.get('events', [])
                    }))
                
            except asyncio.TimeoutError:
                # Send keep-alive ping
                await websocket.send_text(json.dumps({
                    'type': 'keep_alive',
                    'timestamp': datetime.now().isoformat()
                }))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        # Clean up
        if client_id in active_websockets:
            del active_websockets[client_id]

async def notify_websocket_clients(event_type: str, data: Dict[str, Any]):
    """Notify all connected WebSocket clients"""
    if not active_websockets:
        return
    
    message = {
        'type': event_type,
        'timestamp': datetime.now().isoformat(),
        'data': data
    }
    
    message_text = json.dumps(message)
    
    # Send to all connected clients
    disconnected_clients = []
    for client_id, websocket in active_websockets.items():
        try:
            await websocket.send_text(message_text)
        except Exception as e:
            logger.warning(f"Failed to send message to client {client_id}: {e}")
            disconnected_clients.append(client_id)
    
    # Clean up disconnected clients
    for client_id in disconnected_clients:
        if client_id in active_websockets:
            del active_websockets[client_id]
