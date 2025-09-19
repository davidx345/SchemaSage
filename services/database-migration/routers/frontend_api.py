"""
Frontend API Compatibility Router
Provides the exact API endpoints expected by the frontend application
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import logging
import uuid
import asyncio
from datetime import datetime

"""
Frontend API Compatibility Router
Provides the exact API endpoints expected by the frontend application
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import logging
import uuid
import asyncio
from datetime import datetime
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/database", tags=["Frontend Database API"])

# Store for background jobs
import_jobs = {}

class ConnectionURLParser:
    """Simplified connection URL parser for frontend compatibility"""
    
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
    """Mock database connection manager for frontend compatibility"""
    
    async def test_connection(self, connection_url: str) -> Dict[str, Any]:
        """Mock connection test"""
        try:
            parsed = ConnectionURLParser.parse_connection_url(connection_url)
            
            # Simulate connection test
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Mock successful connection for demo purposes
            return {
                "status": "success",
                "connection_time": 0.15,
                "version": self._get_mock_version(parsed.get('db_type')),
                "server_info": {
                    "type": parsed.get('db_type'),
                    "host": parsed.get('host'),
                    "port": parsed.get('port'),
                    "database": parsed.get('database')
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connection_time": 0
            }
    
    def _get_mock_version(self, db_type: str) -> str:
        """Get mock version string for database type"""
        versions = {
            "postgresql": "PostgreSQL 14.2",
            "mysql": "MySQL 8.0.28",
            "mongodb": "MongoDB 5.0.6",
            "sqlite": "SQLite 3.38.0",
            "redis": "Redis 6.2.6"
        }
        return versions.get(db_type, "Unknown")

# Initialize mock manager
connection_manager = MockDatabaseConnectionManager()

@router.post("/test-connection-url")
async def test_connection_url(request: Dict[str, Any]):
    """
    Test database connection using connection URL
    
    Expected Request Body:
    {
        "connection_url": "postgresql://user:pass@host:port/dbname",
        "type": "postgresql"
    }
    
    Expected Response:
    {
        "success": true,
        "message": "Connection successful",
        "databaseType": "postgresql", 
        "metadata": {
            "version": "14.2",
            "host": "localhost"
        }
    }
    """
    try:
        connection_url = request.get("connection_url")
        db_type = request.get("type")
        
        if not connection_url:
            raise HTTPException(status_code=400, detail="connection_url is required")
        
        logger.info(f"Testing connection: {ConnectionURLParser.mask_sensitive_data(connection_url)}")
        
        # Validate URL format
        is_valid, error_message = ConnectionURLParser.validate_connection_url(connection_url)
        if not is_valid:
            return {
                "success": False,
                "message": f"Invalid connection URL: {error_message}",
                "databaseType": db_type,
                "metadata": {}
            }
        
        # Parse connection details
        parsed_params = ConnectionURLParser.parse_connection_url(connection_url)
        
        # Test connection
        test_result = await connection_manager.test_connection(connection_url)
        
        if test_result.get('status') == 'success':
            return {
                "success": True,
                "message": "Connection successful",
                "databaseType": parsed_params.get('db_type', db_type),
                "metadata": {
                    "version": test_result.get('version', 'Unknown'),
                    "host": parsed_params.get('host', 'Unknown'),
                    "port": parsed_params.get('port', 'Unknown'),
                    "database": parsed_params.get('database', 'Unknown'),
                    "connection_time": test_result.get('connection_time', 0),
                    "ssl_enabled": parsed_params.get('ssl_enabled', False)
                }
            }
        else:
            return {
                "success": False,
                "message": test_result.get('error', 'Connection failed'),
                "databaseType": parsed_params.get('db_type', db_type),
                "metadata": {
                    "host": parsed_params.get('host', 'Unknown'),
                    "error_details": test_result.get('error', 'Unknown error')
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "databaseType": db_type or "unknown",
            "metadata": {
                "error": str(e)
            }
        }

@router.post("/import-schema-url")
async def import_schema_url(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Import schema from database using connection URL
    
    Expected Request Body:
    {
        "connection_url": "postgresql://user:pass@host:port/dbname",
        "type": "postgresql"
    }
    
    Expected Response:
    {
        "success": true,
        "data": {
            "tables": [...],
            "relationships": [...],
            "metadata": {...}
        }
    }
    """
    try:
        connection_url = request.get("connection_url")
        db_type = request.get("type")
        
        if not connection_url:
            raise HTTPException(status_code=400, detail="connection_url is required")
        
        logger.info(f"Importing schema: {ConnectionURLParser.mask_sensitive_data(connection_url)}")
        
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
        
        # Import schema based on database type
        schema_data = await import_schema_by_type(connection_url, parsed_params.get('db_type', db_type))
        
        return {
            "success": True,
            "message": "Schema imported successfully",
            "data": {
                "tables": schema_data.get('tables', []),
                "relationships": schema_data.get('relationships', []),
                "views": schema_data.get('views', []),
                "indexes": schema_data.get('indexes', []),
                "functions": schema_data.get('functions', []),
                "metadata": {
                    "database_type": parsed_params.get('db_type', db_type),
                    "database_name": parsed_params.get('database'),
                    "host": parsed_params.get('host'),
                    "import_timestamp": datetime.utcnow().isoformat(),
                    "table_count": len(schema_data.get('tables', [])),
                    "relationship_count": len(schema_data.get('relationships', []))
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing schema: {e}")
        return {
            "success": False,
            "message": f"Schema import failed: {str(e)}",
            "data": {
                "error": str(e)
            }
        }

async def import_schema_by_type(connection_url: str, db_type: str) -> Dict[str, Any]:
    """Import schema based on database type"""
    
    # For now, return sample schema data
    # In a real implementation, this would connect to the actual database
    # and extract the schema information
    
    sample_schemas = {
        "postgresql": {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "integer", "primary_key": True, "nullable": False},
                        {"name": "email", "type": "varchar(255)", "primary_key": False, "nullable": False},
                        {"name": "name", "type": "varchar(100)", "primary_key": False, "nullable": True},
                        {"name": "created_at", "type": "timestamp", "primary_key": False, "nullable": False}
                    ]
                },
                {
                    "name": "orders",
                    "columns": [
                        {"name": "id", "type": "integer", "primary_key": True, "nullable": False},
                        {"name": "user_id", "type": "integer", "primary_key": False, "nullable": False},
                        {"name": "total", "type": "decimal(10,2)", "primary_key": False, "nullable": False},
                        {"name": "status", "type": "varchar(50)", "primary_key": False, "nullable": False}
                    ]
                }
            ],
            "relationships": [
                {
                    "from_table": "orders",
                    "from_column": "user_id", 
                    "to_table": "users",
                    "to_column": "id",
                    "type": "foreign_key"
                }
            ],
            "views": [],
            "indexes": [
                {"table": "users", "column": "email", "type": "unique"},
                {"table": "orders", "column": "user_id", "type": "index"}
            ]
        },
        "mysql": {
            "tables": [
                {
                    "name": "products",
                    "columns": [
                        {"name": "id", "type": "int", "primary_key": True, "nullable": False},
                        {"name": "name", "type": "varchar(255)", "primary_key": False, "nullable": False},
                        {"name": "price", "type": "decimal(10,2)", "primary_key": False, "nullable": False}
                    ]
                }
            ],
            "relationships": [],
            "views": [],
            "indexes": []
        }
    }
    
    # Return sample data or actual imported data
    return sample_schemas.get(db_type, {
        "tables": [],
        "relationships": [],
        "views": [],
        "indexes": []
    })

@router.get("/connections")
async def get_database_connections():
    """
    Get list of saved database connections
    
    Expected Response:
    {
        "success": true,
        "data": {
            "connections": [...],
            "total": 3
        }
    }
    """
    try:
        # Mock connections data for now
        # In a real implementation, this would query saved connections from a database
        
        mock_connections = [
            {
                "id": str(uuid.uuid4()),
                "name": "Production PostgreSQL",
                "type": "postgresql",
                "host": "prod-db.company.com",
                "port": 5432,
                "database": "main_app",
                "username": "app_user",
                "status": "connected",
                "last_tested": "2024-01-16T10:30:00Z",
                "created_at": "2024-01-10T09:00:00Z"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Development MySQL",
                "type": "mysql", 
                "host": "dev-mysql.company.com",
                "port": 3306,
                "database": "dev_app",
                "username": "dev_user",
                "status": "disconnected",
                "last_tested": "2024-01-15T14:20:00Z",
                "created_at": "2024-01-12T11:30:00Z"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Analytics MongoDB",
                "type": "mongodb",
                "host": "analytics-mongo.company.com", 
                "port": 27017,
                "database": "analytics",
                "username": "analytics_user",
                "status": "connected",
                "last_tested": "2024-01-16T16:45:00Z",
                "created_at": "2024-01-08T08:15:00Z"
            }
        ]
        
        return {
            "success": True,
            "data": {
                "connections": mock_connections,
                "total": len(mock_connections),
                "active_connections": len([c for c in mock_connections if c["status"] == "connected"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching connections: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch connections: {str(e)}",
            "data": {}
        }

@router.post("/connections")
async def save_database_connection(request: Dict[str, Any]):
    """
    Save a new database connection
    
    Expected Request Body:
    {
        "name": "My Database",
        "type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "username": "user",
        "password": "pass"
    }
    
    Expected Response:
    {
        "success": true,
        "data": {
            "connection_id": "uuid",
            "message": "Connection saved successfully"
        }
    }
    """
    try:
        name = request.get("name")
        db_type = request.get("type")
        host = request.get("host")
        port = request.get("port")
        database = request.get("database")
        username = request.get("username")
        password = request.get("password")
        
        # Validate required fields
        if not all([name, db_type, host, username, database]):
            raise HTTPException(status_code=400, detail="Missing required connection parameters")
        
        # Test connection first
        if db_type == "sqlite":
            connection_url = f"sqlite:///{database}"
        else:
            port_str = f":{port}" if port else ""
            password_str = f":{password}" if password else ""
            connection_url = f"{db_type}://{username}{password_str}@{host}{port_str}/{database}"
        
        # Test the connection
        test_result = await connection_manager.test_connection(connection_url)
        
        if test_result.get('status') != 'success':
            return {
                "success": False,
                "message": f"Connection test failed: {test_result.get('error')}",
                "data": {}
            }
        
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        
        # In a real implementation, save to database here
        logger.info(f"Saving connection: {name} ({ConnectionURLParser.mask_sensitive_data(connection_url)})")
        
        return {
            "success": True,
            "message": "Connection saved successfully",
            "data": {
                "connection_id": connection_id,
                "name": name,
                "type": db_type,
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving connection: {e}")
        return {
            "success": False,
            "message": f"Failed to save connection: {str(e)}",
            "data": {}
        }

@router.delete("/connections/{connection_id}")
async def delete_database_connection(connection_id: str):
    """
    Delete a saved database connection
    
    Expected Response:
    {
        "success": true,
        "message": "Connection deleted successfully"
    }
    """
    try:
        # In a real implementation, delete from database here
        logger.info(f"Deleting connection: {connection_id}")
        
        return {
            "success": True,
            "message": "Connection deleted successfully",
            "data": {
                "connection_id": connection_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error deleting connection: {e}")
        return {
            "success": False,
            "message": f"Failed to delete connection: {str(e)}",
            "data": {}
        }
async def get_supported_connection_types():
    """Get list of supported database connection types"""
    return {
        "success": True,
        "data": {
            "types": [
                {
                    "id": "postgresql",
                    "name": "PostgreSQL",
                    "description": "PostgreSQL database",
                    "url_format": "postgresql://user:pass@host:port/database",
                    "default_port": 5432
                },
                {
                    "id": "mysql", 
                    "name": "MySQL",
                    "description": "MySQL database",
                    "url_format": "mysql://user:pass@host:port/database",
                    "default_port": 3306
                },
                {
                    "id": "mongodb",
                    "name": "MongoDB", 
                    "description": "MongoDB document database",
                    "url_format": "mongodb://user:pass@host:port/database",
                    "default_port": 27017
                },
                {
                    "id": "sqlite",
                    "name": "SQLite",
                    "description": "SQLite file database",
                    "url_format": "sqlite:///path/to/database.db",
                    "default_port": None
                },
                {
                    "id": "redis",
                    "name": "Redis",
                    "description": "Redis key-value store",
                    "url_format": "redis://user:pass@host:port/database",
                    "default_port": 6379
                }
            ]
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Database Migration Service - Frontend API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Connection URL testing",
            "Schema import from URL",
            "Multiple database support",
            "Error handling",
            "Connection validation"
        ]
    }

# ===== BACKWARD COMPATIBILITY ENDPOINTS =====

@router.post("/test-connection")
async def test_connection_legacy(request: Dict[str, Any]):
    """
    Backward compatibility endpoint for legacy connection testing
    
    Expected Request Body:
    {
        "host": "localhost",
        "port": 5432,
        "username": "user",
        "password": "pass",
        "database": "dbname",
        "type": "postgresql"
    }
    """
    try:
        # Convert legacy format to connection URL
        host = request.get("host")
        port = request.get("port")
        username = request.get("username")
        password = request.get("password")
        database = request.get("database")
        db_type = request.get("type")
        
        if not all([host, username, database, db_type]):
            raise HTTPException(status_code=400, detail="Missing required connection parameters")
        
        # Build connection URL
        if db_type == "sqlite":
            connection_url = f"sqlite:///{database}"
        else:
            port_str = f":{port}" if port else ""
            password_str = f":{password}" if password else ""
            connection_url = f"{db_type}://{username}{password_str}@{host}{port_str}/{database}"
        
        # Use the new connection URL endpoint
        url_request = {
            "connection_url": connection_url,
            "type": db_type
        }
        
        return await test_connection_url(url_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in legacy connection test: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "databaseType": db_type or "unknown",
            "metadata": {"error": str(e)}
        }

@router.post("/import-schema")
async def import_schema_legacy(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Backward compatibility endpoint for legacy schema import
    
    Expected Request Body:
    {
        "host": "localhost",
        "port": 5432,
        "username": "user", 
        "password": "pass",
        "database": "dbname",
        "type": "postgresql"
    }
    """
    try:
        # Convert legacy format to connection URL
        host = request.get("host")
        port = request.get("port")
        username = request.get("username")
        password = request.get("password")
        database = request.get("database")
        db_type = request.get("type")
        
        if not all([host, username, database, db_type]):
            raise HTTPException(status_code=400, detail="Missing required connection parameters")
        
        # Build connection URL
        if db_type == "sqlite":
            connection_url = f"sqlite:///{database}"
        else:
            port_str = f":{port}" if port else ""
            password_str = f":{password}" if password else ""
            connection_url = f"{db_type}://{username}{password_str}@{host}{port_str}/{database}"
        
        # Use the new connection URL endpoint
        url_request = {
            "connection_url": connection_url,
            "type": db_type
        }
        
        return await import_schema_url(url_request, background_tasks)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in legacy schema import: {e}")
        return {
            "success": False,
            "message": f"Schema import failed: {str(e)}",
            "data": {"error": str(e)}
        }
