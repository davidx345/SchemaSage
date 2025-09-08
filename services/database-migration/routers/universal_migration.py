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
        
        if not connection_url:
            raise HTTPException(status_code=400, detail="connection_url is required")
        
        logger.info(f"Testing database connection: {ConnectionURLParser.mask_sensitive_data(connection_url)}")
        
        # Validate URL format first
        is_valid, error_message = ConnectionURLParser.validate_connection_url(connection_url)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid connection URL: {error_message}")
        
        # Test connection
        result = await connection_manager.test_connection(connection_url)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

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
async def import_database_schema(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Import schema from database using connection URL"""
    try:
        connection_url = request.get("connection_url")
        import_options = request.get("import_options", {})
        
        if not connection_url:
            raise HTTPException(status_code=400, detail="connection_url is required")
        
        logger.info(f"Starting schema import: {ConnectionURLParser.mask_sensitive_data(connection_url)}")
        
        # Validate connection URL
        is_valid, error_message = ConnectionURLParser.validate_connection_url(connection_url)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid connection URL: {error_message}")
        
        # Test connection first
        connection_test = await connection_manager.test_connection(connection_url)
        if connection_test['status'] != 'success':
            raise HTTPException(status_code=400, detail=f"Connection failed: {connection_test.get('error')}")
        
        # Create import job
        import_job_id = str(uuid.uuid4())
        db_params = ConnectionURLParser.parse_connection_url(connection_url)
        
        import_job = {
            'job_id': import_job_id,
            'status': 'starting',
            'database_type': db_params['database_type'],
            'connection_id': connection_test['connection_id'],
            'started_at': datetime.now().isoformat(),
            'import_options': import_options,
            'progress': {
                'percentage': 0,
                'current_step': 'initializing',
                'tables_processed': 0,
                'total_tables': 0
            }
        }
        
        # Start background import process
        background_tasks.add_task(
            process_schema_import_task, 
            import_job_id, 
            connection_url, 
            import_options
        )
        
        return {
            'import_job': import_job,
            'message': 'Schema import started successfully',
            'status_endpoint': f'/api/database/import/{import_job_id}/status',
            'cancel_endpoint': f'/api/database/import/{import_job_id}/cancel'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting schema import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start schema import: {str(e)}")

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

@router.get("/import-status/{job_id}")
async def get_import_job_status(job_id: str):
    """Get status of schema import job"""
    try:
        if job_id not in import_jobs:
            raise HTTPException(status_code=404, detail="Import job not found")
        
        job = import_jobs[job_id]
        
        # Add runtime information if job is running
        if job['status'] == 'running':
            started_at = datetime.fromisoformat(job['started_at'])
            elapsed_seconds = (datetime.now() - started_at).total_seconds()
            job['runtime_info'] = {
                'elapsed_seconds': round(elapsed_seconds, 1),
                'estimated_remaining_seconds': max(0, round((100 - job['progress']['percentage']) * 1.5, 1))
            }
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get import job status")

@router.post("/import/{job_id}/cancel")
async def cancel_import_job(job_id: str):
    """Cancel schema import job"""
    try:
        if job_id not in import_jobs:
            raise HTTPException(status_code=404, detail="Import job not found")
        
        job = import_jobs[job_id]
        
        if job['status'] not in ['running', 'starting']:
            raise HTTPException(status_code=400, detail="Cannot cancel job that is not running")
        
        # Update job status
        job.update({
            'status': 'cancelled',
            'cancelled_at': datetime.now().isoformat()
        })
        
        await notify_websocket_clients('import_cancelled', {
            'job_id': job_id,
            'status': 'cancelled'
        })
        
        return {
            'job_id': job_id,
            'status': 'cancelled',
            'message': 'Import job cancelled successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling import job: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel import job")

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
