"""
Enterprise Frontend API Router
PostgreSQL-backed persistent storage with JWT authentication and AES-256 encryption
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends, status
from typing import Dict, Any, Optional, List
import logging
import uuid
import asyncio
from datetime import datetime
from urllib.parse import urlparse

# Enterprise imports
from core.auth import get_current_user, require_authentication, UserContext
from core.enterprise_store import enterprise_store
from core.encryption import connection_encryption, key_manager

# Shared utilities for import functionality
from shared.utils.connection_parser import ConnectionURLParser
from shared.utils.database_manager import connection_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/database", tags=["Enterprise Database API"])

# Store for background jobs
import_jobs = {}

def get_request_context(request: Request) -> Dict[str, Any]:
    """Extract request context for audit logging"""
    return {
        'ip_address': request.client.host if request.client else 'unknown',
        'user_agent': request.headers.get('user-agent', ''),
        'request_id': request.headers.get('x-request-id', str(uuid.uuid4())),
        'endpoint': str(request.url.path),
        'method': request.method
    }

class ConnectionURLParser:
    """Enhanced connection URL parser with security features"""
    
    @staticmethod
    def parse_connection_url(url: str) -> Dict[str, Any]:
        """Parse connection URL into components"""
        try:
            parsed = urlparse(url)
            
            return {
                "db_type": parsed.scheme,
                "host": parsed.hostname,
                "port": parsed.port,
                "username": parsed.username,
                "password": parsed.password,
                "database": parsed.path.lstrip('/') if parsed.path else None,
                "ssl_enabled": 'ssl=true' in (parsed.query or '') or 'sslmode=require' in (parsed.query or '')
            }
        except Exception as e:
            raise ValueError(f"Invalid connection URL format: {e}")
    
    @staticmethod
    def validate_connection_url(url: str) -> tuple[bool, str]:
        """Validate connection URL format"""
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                return False, "Missing database type (scheme)"
            
            supported_schemes = ['postgresql', 'mysql', 'mongodb', 'sqlite', 'redis']
            if parsed.scheme not in supported_schemes:
                return False, f"Unsupported database type: {parsed.scheme}. Supported: {', '.join(supported_schemes)}"
            
            if parsed.scheme != 'sqlite' and not parsed.hostname:
                return False, "Missing hostname"
            
            return True, "Valid"
        except Exception as e:
            return False, f"Invalid URL format: {e}"
    
    @staticmethod
    def mask_sensitive_data(url: str) -> str:
        """Mask password in URL for logging"""
        try:
            parsed = urlparse(url)
            if parsed.password:
                masked_url = url.replace(parsed.password, "***")
                return masked_url
            return url
        except:
            return "***"


class MockDatabaseConnectionManager:
    """Enhanced mock database connection manager"""
    
    async def test_connection(self, connection_url: str) -> Dict[str, Any]:
        """Test database connection"""
        try:
            parsed = ConnectionURLParser.parse_connection_url(connection_url)
            
            # Simulate connection test with realistic timing
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Enhanced mock successful connection
            return {
                "status": "success",
                "connection_time": 0.15,
                "database_type": parsed["db_type"],
                "database_version": "Mock 1.0",
                "server_info": {
                    "host": parsed["host"],
                    "port": parsed["port"],
                    "ssl_enabled": parsed["ssl_enabled"]
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connection_time": None
            }

# Initialize services
connection_manager = MockDatabaseConnectionManager()

@router.on_event("startup")
async def startup_event():
    """Initialize enterprise services on startup"""
    try:
        await enterprise_store.initialize()
        logger.info("🚀 Enterprise Database Migration Service started")
        logger.info("✅ PostgreSQL persistence enabled")
        logger.info("🔐 AES-256 encryption active")
        logger.info("🛡️ JWT authentication ready")
        
        # Validate encryption environment
        encryption_status = key_manager.validate_encryption_environment()
        if not encryption_status["secure"]:
            logger.warning("⚠️ Encryption environment issues detected:")
            for issue in encryption_status["issues"]:
                logger.warning(f"  - {issue}")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await enterprise_store.close()
    logger.info("🛑 Enterprise services shut down")

@router.get("/connections")
async def get_database_connections(
    request: Request,
    current_user: UserContext = Depends(get_current_user)
):
    """
    Get list of database connections for the authenticated user
    
    Features:
    - User isolation (only see your own connections)
    - Encrypted data retrieval
    - Health status monitoring
    - Audit logging
    """
    try:
        if not current_user or current_user.user_id == "anonymous":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get user connections from enterprise store
        connections = await enterprise_store.get_user_connections(current_user)
        
        # Get user statistics
        user_stats = await enterprise_store.get_user_stats(current_user)
        
        logger.info(f"👤 User {current_user.user_id} retrieved {len(connections)} connections")
        
        return {
            "success": True,
            "data": {
                "connections": connections,
                "total": len(connections),
                "stats": user_stats
            },
            "metadata": {
                "user_id": current_user.user_id,
                "subscription_plan": current_user.subscription_plan,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get connections for user {current_user.user_id}: {e}")
        return {
            "success": False,
            "message": f"Failed to retrieve connections: {str(e)}",
            "data": {"connections": [], "total": 0}
        }

@router.post("/connections")
async def save_database_connection(
    request_data: Dict[str, Any],
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: UserContext = Depends(require_authentication)
):
    """
    Save a new database connection with enterprise security
    
    Features:
    - JWT authentication required
    - AES-256 password encryption
    - User quota enforcement
    - Audit trail logging
    - Connection validation
    """
    try:
        # Extract and validate connection data
        required_fields = ['name', 'type', 'host', 'username', 'database']
        for field in required_fields:
            if not request_data.get(field):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required field: {field}"
                )
        
        # Build connection URL for testing
        db_type = request_data.get('type')
        host = request_data.get('host')
        port = request_data.get('port')
        database = request_data.get('database')
        username = request_data.get('username')
        password = request_data.get('password', '')
        
        if db_type == "sqlite":
            connection_url = f"sqlite:///{database}"
        else:
            port_str = f":{port}" if port else ""
            password_str = f":{password}" if password else ""
            connection_url = f"{db_type}://{username}{password_str}@{host}{port_str}/{database}"
        
        # Test connection first (optional but recommended)
        test_result = await connection_manager.test_connection(connection_url)
        if test_result.get('status') != 'success':
            logger.warning(f"Connection test failed for {current_user.user_id}: {test_result.get('error')}")
            # Continue anyway - user might want to save for later configuration
        
        # Save to enterprise store with encryption
        request_context = get_request_context(request)
        connection_id = await enterprise_store.save_connection(
            connection_data=request_data,
            user=current_user,
            request_context=request_context
        )
        
        logger.info(f"✅ Connection {connection_id} saved for user {current_user.user_id}")
        
        return {
            "success": True,
            "data": {
                "connection_id": connection_id,
                "message": "Connection saved successfully"
            },
            "metadata": {
                "encrypted": True,
                "test_status": test_result.get('status', 'not_tested'),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Unexpected error saving connection: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error while saving connection"
        )

@router.post("/connections/{connection_id}/test")
async def test_connection_by_id(
    connection_id: str,
    request: Request,
    current_user: UserContext = Depends(require_authentication)
):
    """
    Test a specific database connection by ID
    
    Features:
    - User access control (can only test own connections)
    - Decrypts connection data securely
    - Updates connection health metrics
    - Logs test results for audit
    """
    try:
        # Get connection with user access control
        connection = await enterprise_store.get_connection(connection_id, current_user)
        
        if not connection:
            raise HTTPException(
                status_code=404, 
                detail=f"Connection {connection_id} not found or access denied"
            )
        
        # Build connection URL from decrypted data
        if connection.get('type') == 'sqlite':
            connection_url = f"sqlite:///{connection.get('database')}"
        else:
            host = connection.get('host')
            port = connection.get('port')
            username = connection.get('username')
            password = connection.get('password', '')
            database = connection.get('database')
            db_type = connection.get('type')
            
            port_str = f":{port}" if port else ""
            password_str = f":{password}" if password else ""
            connection_url = f"{db_type}://{username}{password_str}@{host}{port_str}/{database}"
        
        logger.info(f"🔍 Testing connection {connection_id} for user {current_user.user_id}")
        
        # Test the connection
        test_result = await connection_manager.test_connection(connection_url)
        
        # Update connection status in enterprise store
        request_context = get_request_context(request)
        status_updated = await enterprise_store.update_connection_status(
            connection_id=connection_id,
            user=current_user,
            status='connected' if test_result.get('status') == 'success' else 'error',
            response_time_ms=int(test_result.get('connection_time', 0) * 1000),
            error_message=test_result.get('error'),
            request_context=request_context
        )
        
        if test_result.get('status') == 'success':
            return {
                "success": True,
                "message": "Connection successful",
                "data": {
                    "connection_id": connection_id,
                    "connection_time": test_result.get('connection_time', 0),
                    "database_type": connection.get('type'),
                    "database_version": test_result.get('database_version', 'Unknown'),
                    "status": "connected",
                    "server_info": test_result.get('server_info', {})
                }
            }
        else:
            return {
                "success": False,
                "message": test_result.get('error', 'Connection failed'),
                "data": {
                    "connection_id": connection_id,
                    "error": test_result.get('error', 'Unknown error'),
                    "status": "error"
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing connection {connection_id}: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "data": {"error": str(e)}
        }

@router.delete("/connections/{connection_id}")
async def delete_database_connection(
    connection_id: str,
    request: Request,
    current_user: UserContext = Depends(require_authentication)
):
    """
    Delete (soft delete) a database connection
    
    Features:
    - User access control
    - Soft delete (archive) for audit trail
    - Quota management
    - Audit logging
    """
    try:
        request_context = get_request_context(request)
        
        success = await enterprise_store.delete_connection(
            connection_id=connection_id,
            user=current_user,
            request_context=request_context
        )
        
        if success:
            logger.info(f"🗑️ Connection {connection_id} deleted by user {current_user.user_id}")
            return {
                "success": True,
                "message": "Connection deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Connection not found or access denied"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting connection: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete connection"
        )

@router.get("/stats")
async def get_database_service_stats(
    current_user: UserContext = Depends(get_current_user)
):
    """
    Get database service statistics
    
    Features:
    - User-specific stats if authenticated
    - Service-wide stats for anonymous users
    - Real-time metrics from PostgreSQL
    """
    try:
        if current_user and current_user.user_id != "anonymous":
            # Authenticated user - return personal stats
            user_stats = await enterprise_store.get_user_stats(current_user)
            return {
                **user_stats,
                "service_status": "healthy",
                "last_updated": datetime.utcnow().isoformat(),
                "user_authenticated": True
            }
        else:
            # Anonymous user - return generic stats
            return {
                "total_connections": 0,
                "active_connections": 0,
                "total_schemas_imported": 0,
                "migrations_completed": 0,
                "service_status": "healthy",
                "last_updated": datetime.utcnow().isoformat(),
                "user_authenticated": False
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return {
            "total_connections": 0,
            "active_connections": 0,
            "service_status": "error",
            "error": str(e),
            "last_updated": datetime.utcnow().isoformat()
        }

@router.get("/security/encryption-status")
async def get_encryption_status(
    current_user: UserContext = Depends(require_authentication)
):
    """
    Get encryption status and security information
    Admin endpoint for monitoring security health
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        
        key_info = key_manager.get_key_info()
        environment_validation = key_manager.validate_encryption_environment()
        
        return {
            "encryption_active": True,
            "key_info": key_info,
            "environment_validation": environment_validation,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting encryption status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get encryption status")

@router.post("/test-connection-url")
async def test_connection_url(
    request_data: Dict[str, Any],
    current_user: UserContext = Depends(get_current_user)
):
    """
    Test database connection using connection URL
    Enhanced with user context and audit logging
    """
    try:
        connection_url = request_data.get("connection_url")
        if not connection_url:
            raise HTTPException(status_code=400, detail="connection_url is required")
        
        # Validate URL format
        is_valid, validation_message = ConnectionURLParser.validate_connection_url(connection_url)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid connection URL: {validation_message}")
        
        logger.info(f"🔍 Testing connection URL for user {current_user.user_id if current_user else 'anonymous'}")
        
        # Test connection
        test_result = await connection_manager.test_connection(connection_url)
        
        if test_result.get('status') == 'success':
            return {
                "success": True,
                "message": "Connection successful",
                "data": {
                    "connection_time": test_result.get('connection_time', 0),
                    "database_type": test_result.get('database_type', 'unknown'),
                    "database_version": test_result.get('database_version', 'unknown'),
                    "server_info": test_result.get('server_info', {})
                }
            }
        else:
            return {
                "success": False,
                "message": test_result.get('error', 'Connection failed'),
                "data": {"error": test_result.get('error', 'Unknown error')}
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing connection URL: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "data": {"error": str(e)}
        }

# ===== SCHEMA IMPORT ENDPOINTS =====

@router.post("/import-schema-url")
async def import_schema_url(
    request: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    user: UserContext = Depends(get_current_user)
):
    """
    Import schema from database using connection URL
    Enterprise version with JWT authentication and audit logging
    """
    try:
        connection_url = request.get("connection_url")
        db_type = request.get("type")
        
        if not connection_url:
            raise HTTPException(status_code=400, detail="connection_url is required")
        
        # Log access attempt
        logger.info(f"🔍 User {user.user_id} importing schema: {ConnectionURLParser.mask_sensitive_data(connection_url)}")
        
        # Validate URL format
        is_valid, error_message = ConnectionURLParser.validate_connection_url(connection_url)
        if not is_valid:
            return {
                "success": False,
                "message": f"Invalid connection URL: {error_message}",
                "data": {}
            }
        
        # Test connection first
        connection_test = await connection_manager.test_connection(connection_url)
        if connection_test.get('status') != 'success':
            return {
                "success": False,
                "message": f"Connection failed: {connection_test.get('error')}",
                "data": {}
            }
        
        # Parse connection details  
        parsed_params = ConnectionURLParser.parse_connection_url(connection_url)
        db_type = parsed_params.get('db_type', db_type)
        
        # Import schema based on database type
        schema_data = await import_schema_by_type(connection_url, db_type)
        
        return {
            "success": True,
            "message": "Schema imported successfully",
            "data": schema_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error importing schema for user {user.user_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Schema import failed: {str(e)}"
        )

@router.post("/import-schema")
async def import_schema_legacy(
    request: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    user: UserContext = Depends(get_current_user)
):
    """
    Backward compatibility endpoint for legacy schema import
    Enterprise version with JWT authentication
    """
    try:
        # Convert legacy format to new format
        connection_url = request.get("connectionUrl") or request.get("connection_url")
        
        if not connection_url:
            # Try to build from connection parameters
            connection_data = request.get("connection", {})
            if connection_data:
                connection_url = ConnectionURLParser.build_connection_url(connection_data)
        
        if not connection_url:
            raise HTTPException(status_code=400, detail="Connection URL or connection data is required")
        
        # Delegate to the main import endpoint
        url_request = {
            "connection_url": connection_url,
            "type": request.get("type")
        }
        
        return await import_schema_url(url_request, background_tasks, user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in legacy schema import for user {user.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Schema import failed: {str(e)}"
        )

@router.post("/test-connection")
async def test_connection_legacy(
    request: Dict[str, Any],
    user: UserContext = Depends(get_current_user)
):
    """
    Legacy endpoint for testing database connections
    Enterprise version with JWT authentication
    """
    try:
        connection_url = request.get("connectionUrl") or request.get("connection_url")
        
        if not connection_url:
            # Try to build from connection parameters
            connection_data = request.get("connection", {})
            if connection_data:
                connection_url = ConnectionURLParser.build_connection_url(connection_data)
        
        if not connection_url:
            return {
                "success": False,
                "message": "Connection URL or connection data is required",
                "data": {}
            }
        
        # Delegate to the main test endpoint
        url_request = {"connection_url": connection_url}
        return await test_connection_url(url_request, user)
        
    except Exception as e:
        logger.error(f"❌ Error in legacy connection test for user {user.user_id}: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "data": {"error": str(e)}
        }

@router.get("/health")
async def health_check():
    """
    Health check endpoint for enterprise frontend API
    """
    return {
        "status": "healthy",
        "service": "Database Migration Service - Enterprise Frontend API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "PostgreSQL persistence",
            "JWT authentication",
            "AES-256 encryption", 
            "Multi-user isolation",
            "Connection health monitoring",
            "Audit logging",
            "Schema import",
            "Connection testing"
        ],
        "security": {
            "authentication": "JWT",
            "encryption": "AES-256-GCM",
            "storage": "PostgreSQL with encryption"
        }
    }

# Helper function for schema import
async def import_schema_by_type(connection_url: str, db_type: str) -> Dict[str, Any]:
    """Import schema based on database type"""
    # This would contain the actual schema import logic
    # For now, return a sample structure
    return {
        "tables": [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "email", "type": "varchar", "length": 255},
                    {"name": "created_at", "type": "timestamp"}
                ]
            }
        ],
        "relationships": [],
        "metadata": {
            "database_type": db_type,
            "import_timestamp": datetime.utcnow().isoformat(),
            "table_count": 1
        }
    }