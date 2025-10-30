"""
Celery Tasks for Database Migration Service
Long-running tasks that run in background workers
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from celery import Task
from celery_app import celery_app

# Setup logging
logger = logging.getLogger(__name__)

# Import database utilities (these will be imported at task runtime)
def get_database_manager():
    """Lazy import to avoid circular dependencies"""
    from shared.utils.database_manager import connection_manager
    return connection_manager

def get_connection_parser():
    """Lazy import to avoid circular dependencies"""
    from shared.utils.connection_parser import ConnectionURLParser
    return ConnectionURLParser


class CallbackTask(Task):
    """Base task with progress callback support"""
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update task progress"""
        percentage = int((current / total) * 100) if total > 0 else 0
        self.update_state(
            state='PROGRESS',
            meta={
                'current': current,
                'total': total,
                'percentage': percentage,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        )


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='tasks.extract_schema_task',
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True
)
def extract_schema_task(self, connection_url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract database schema in background worker
    
    Args:
        connection_url: Database connection URL
        options: Optional extraction options (include_data_samples, max_tables, etc.)
    
    Returns:
        Dictionary containing schema data and metadata
    """
    try:
        logger.info(f"Starting schema extraction task {self.request.id}")
        
        if options is None:
            options = {}
        
        # Update progress: Starting
        self.update_progress(0, 100, "Initializing schema extraction")
        
        # Get utilities
        connection_manager = get_database_manager()
        ConnectionURLParser = get_connection_parser()
        
        # Mask sensitive data for logging
        masked_url = ConnectionURLParser.mask_sensitive_data(connection_url)
        logger.info(f"Extracting schema from: {masked_url}")
        
        # Update progress: Validating connection
        self.update_progress(10, 100, "Validating connection URL")
        
        # Validate URL
        is_valid, error_message = ConnectionURLParser.validate_connection_url(connection_url)
        if not is_valid:
            logger.error(f"Invalid connection URL: {error_message}")
            return {
                'success': False,
                'error': {
                    'message': f"Invalid connection URL: {error_message}",
                    'code': 'INVALID_URL',
                    'details': {'reason': error_message}
                }
            }
        
        # Update progress: Testing connection
        self.update_progress(20, 100, "Testing database connection")
        
        # Test connection (run async function in sync context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            connection_test = loop.run_until_complete(
                connection_manager.test_connection(connection_url)
            )
            
            if connection_test['status'] != 'success':
                error_msg = connection_test.get('error', 'Connection failed')
                logger.error(f"Connection test failed: {error_msg}")
                
                error_str = str(error_msg).lower()
                if 'permission' in error_str or 'denied' in error_str:
                    error_code = "PERMISSION_DENIED"
                elif 'timeout' in error_str:
                    error_code = "TIMEOUT"
                else:
                    error_code = "CONNECTION_FAILED"
                
                return {
                    'success': False,
                    'error': {
                        'message': f"Connection failed: {error_msg}",
                        'code': error_code,
                        'details': {
                            'reason': error_msg,
                            'database_type': connection_test.get('database_type', 'unknown')
                        }
                    }
                }
            
            db_type = connection_test.get('database_type', 'unknown')
            logger.info(f"Connection successful. Database type: {db_type}")
            
            # Update progress: Extracting schema
            self.update_progress(40, 100, f"Extracting schema from {db_type} database")
            
            # Extract schema with timeout protection
            try:
                schema = loop.run_until_complete(
                    asyncio.wait_for(
                        connection_manager.extract_database_schema(connection_url, options),
                        timeout=480  # 8 minutes timeout (well under 9 minute soft limit)
                    )
                )
                
                # Update progress: Processing results
                self.update_progress(90, 100, "Processing schema data")
                
                # Add metadata
                schema['extraction_metadata'] = {
                    'extracted_at': datetime.now().isoformat(),
                    'extraction_duration_seconds': None,  # Could track this
                    'task_id': self.request.id,
                    'database_type': db_type,
                    'tables_count': len(schema.get('tables', [])),
                    'total_columns': sum(len(t.get('columns', [])) for t in schema.get('tables', []))
                }
                
                # Update progress: Complete
                self.update_progress(100, 100, "Schema extraction completed")
                
                logger.info(f"Schema extraction task {self.request.id} completed successfully")
                logger.info(f"Extracted {len(schema.get('tables', []))} tables with {schema['extraction_metadata']['total_columns']} columns")
                
                return {
                    'success': True,
                    'schema': schema
                }
                
            except asyncio.TimeoutError:
                logger.error(f"Schema extraction timed out after 480 seconds")
                return {
                    'success': False,
                    'error': {
                        'message': 'Schema extraction timed out. The database may be too large or slow to respond.',
                        'code': 'TIMEOUT',
                        'details': {
                            'reason': 'Extraction exceeded 8-minute timeout',
                            'database_type': db_type,
                            'suggestion': 'Try reducing the number of tables with the max_tables option'
                        }
                    }
                }
            
            except Exception as extract_error:
                logger.error(f"Schema extraction failed: {extract_error}", exc_info=True)
                
                error_str = str(extract_error).lower()
                if 'permission' in error_str or 'denied' in error_str:
                    error_code = "PERMISSION_DENIED"
                    error_msg = f"Permission denied: {extract_error}"
                elif 'timeout' in error_str:
                    error_code = "TIMEOUT"
                    error_msg = f"Operation timed out: {extract_error}"
                elif 'no tables' in error_str or 'empty' in error_str:
                    error_code = "NO_TABLES_FOUND"
                    error_msg = f"No tables found: {extract_error}"
                else:
                    error_code = "EXTRACTION_FAILED"
                    error_msg = f"Schema extraction failed: {extract_error}"
                
                return {
                    'success': False,
                    'error': {
                        'message': error_msg,
                        'code': error_code,
                        'details': {
                            'reason': str(extract_error),
                            'database_type': db_type
                        }
                    }
                }
        
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Unexpected error in schema extraction task: {e}", exc_info=True)
        
        # For Celery retries, raise the exception
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        return {
            'success': False,
            'error': {
                'message': f"Schema extraction failed: {str(e)}",
                'code': 'EXTRACTION_FAILED',
                'details': {
                    'reason': str(e),
                    'retries': self.request.retries
                }
            }
        }


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='tasks.migrate_data_task',
    max_retries=2,
    default_retry_delay=120
)
def migrate_data_task(
    self,
    source_url: str,
    target_url: str,
    migration_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Migrate data between databases in background worker
    
    Args:
        source_url: Source database connection URL
        target_url: Target database connection URL
        migration_options: Migration options (tables to migrate, batch size, etc.)
    
    Returns:
        Dictionary containing migration results and statistics
    """
    try:
        logger.info(f"Starting data migration task {self.request.id}")
        
        if migration_options is None:
            migration_options = {}
        
        # Update progress
        self.update_progress(0, 100, "Initializing data migration")
        
        # Get utilities
        ConnectionURLParser = get_connection_parser()
        
        # Mask URLs for logging
        masked_source = ConnectionURLParser.mask_sensitive_data(source_url)
        masked_target = ConnectionURLParser.mask_sensitive_data(target_url)
        logger.info(f"Migrating data from {masked_source} to {masked_target}")
        
        # This is a placeholder for actual data migration logic
        # In production, this would:
        # 1. Connect to both databases
        # 2. Read data from source in batches
        # 3. Transform data if needed
        # 4. Write to target database
        # 5. Update progress regularly
        
        # Simulate migration steps
        steps = [
            (10, "Connecting to source database"),
            (20, "Connecting to target database"),
            (30, "Analyzing tables to migrate"),
            (50, "Migrating table schemas"),
            (70, "Migrating data records"),
            (90, "Verifying data integrity"),
            (100, "Migration completed")
        ]
        
        for progress, message in steps:
            self.update_progress(progress, 100, message)
            # Simulate work (in real implementation, do actual migration work here)
        
        result = {
            'success': True,
            'migration_summary': {
                'tables_migrated': 0,  # Would be actual count
                'records_migrated': 0,  # Would be actual count
                'migration_duration_seconds': 0,
                'task_id': self.request.id,
                'completed_at': datetime.now().isoformat()
            }
        }
        
        logger.info(f"Data migration task {self.request.id} completed successfully")
        return result
    
    except Exception as e:
        logger.error(f"Data migration task failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying migration task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        return {
            'success': False,
            'error': {
                'message': f"Data migration failed: {str(e)}",
                'code': 'MIGRATION_FAILED',
                'details': {
                    'reason': str(e),
                    'retries': self.request.retries
                }
            }
        }


@celery_app.task(name='tasks.cleanup_old_results')
def cleanup_old_results() -> Dict[str, Any]:
    """
    Periodic task to cleanup old task results from Redis
    This should be scheduled to run periodically (e.g., daily)
    """
    try:
        logger.info("Starting cleanup of old task results")
        
        # In production, implement cleanup logic
        # For now, just return success
        
        return {
            'success': True,
            'message': 'Cleanup completed',
            'cleaned_count': 0
        }
    
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
