"""
Universal Database Connection Manager
Handles connections to all supported database types with connection pooling
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import json
import hashlib
from contextlib import asynccontextmanager

try:
    import asyncpg
except ImportError:
    asyncpg = None

try:
    import aiomysql
except ImportError:
    aiomysql = None

try:
    import motor.motor_asyncio
except ImportError:
    motor = None

try:
    import aiosqlite
except ImportError:
    aiosqlite = None

try:
    import aioredis
except ImportError:
    aioredis = None

from shared.utils.connection_parser import ConnectionURLParser

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Manages database connections with pooling and health monitoring"""
    
    def __init__(self):
        self.connections = {}
        self.connection_pools = {}
        self.health_status = {}
        self.last_health_check = {}
        
    async def test_connection(self, connection_url: str) -> Dict[str, Any]:
        """
        Test database connection and return connection details
        
        Args:
            connection_url: Database connection URL
            
        Returns:
            Connection test results with metadata
        """
        start_time = datetime.now()
        connection_id = self._generate_connection_id(connection_url)
        
        try:
            # Parse connection URL
            params = ConnectionURLParser.parse_connection_url(connection_url)
            db_type = params['database_type']
            
            logger.info(f"Testing {db_type} connection: {ConnectionURLParser.mask_sensitive_data(connection_url)}")
            
            # Test connection based on database type
            if db_type == 'postgresql':
                result = await self._test_postgresql_connection(params)
            elif db_type == 'mysql':
                result = await self._test_mysql_connection(params)
            elif db_type == 'mongodb':
                result = await self._test_mongodb_connection(params)
            elif db_type == 'sqlite':
                result = await self._test_sqlite_connection(params)
            elif db_type == 'redis':
                result = await self._test_redis_connection(params)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            # Calculate connection time
            connection_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Store health status
            self.health_status[connection_id] = {
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'response_time_ms': connection_time,
                'database_type': db_type
            }
            
            return {
                'status': 'success',
                'connection_id': connection_id,
                'database_type': db_type,
                'connection_time_ms': round(connection_time, 2),
                'server_info': result.get('server_info', {}),
                'connection_details': result.get('connection_details', {}),
                'capabilities': result.get('capabilities', []),
                'tested_at': start_time.isoformat(),
                'message': 'Connection successful'
            }
            
        except Exception as e:
            error_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Store error status
            self.health_status[connection_id] = {
                'status': 'error',
                'last_check': datetime.now().isoformat(),
                'error': str(e),
                'database_type': params.get('database_type', 'unknown')
            }
            
            logger.error(f"Connection test failed: {str(e)}")
            
            return {
                'status': 'failed',
                'connection_id': connection_id,
                'database_type': params.get('database_type', 'unknown'),
                'connection_time_ms': round(error_time, 2),
                'error': str(e),
                'error_type': type(e).__name__,
                'tested_at': start_time.isoformat(),
                'message': 'Connection failed',
                'troubleshooting_tips': self._get_troubleshooting_tips(str(e), params.get('database_type'))
            }
    
    async def _test_postgresql_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test PostgreSQL connection"""
        if not asyncpg:
            raise ImportError("asyncpg not installed. Install with: pip install asyncpg")
        
        try:
            # Build connection string
            conn_str = f"postgresql://{params['username']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
            
            # Test connection
            conn = await asyncpg.connect(conn_str, timeout=30)
            
            # Get server info
            server_version = await conn.fetchval('SELECT version()')
            current_database = await conn.fetchval('SELECT current_database()')
            current_user = await conn.fetchval('SELECT current_user')
            
            # Get database size
            db_size_query = "SELECT pg_size_pretty(pg_database_size(current_database()))"
            db_size = await conn.fetchval(db_size_query)
            
            # Get connection count
            conn_count_query = "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
            connection_count = await conn.fetchval(conn_count_query)
            
            await conn.close()
            
            return {
                'server_info': {
                    'version': server_version,
                    'database': current_database,
                    'user': current_user,
                    'database_size': db_size,
                    'active_connections': connection_count
                },
                'connection_details': {
                    'host': params['host'],
                    'port': params['port'],
                    'ssl_mode': params.get('ssl_mode', 'prefer'),
                    'schema': params.get('schema', 'public')
                },
                'capabilities': [
                    'schemas', 'foreign_keys', 'triggers', 'functions', 
                    'views', 'indexes', 'constraints', 'jsonb', 'arrays'
                ]
            }
            
        except Exception as e:
            raise Exception(f"PostgreSQL connection failed: {str(e)}")
    
    async def _test_mysql_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test MySQL connection"""
        if not aiomysql:
            raise ImportError("aiomysql not installed. Install with: pip install aiomysql")
        
        try:
            # Create connection
            conn = await aiomysql.connect(
                host=params['host'],
                port=params['port'],
                user=params['username'],
                password=params['password'],
                db=params['database'],
                connect_timeout=30
            )
            
            async with conn.cursor() as cursor:
                # Get server info
                await cursor.execute("SELECT VERSION()")
                version = await cursor.fetchone()
                
                await cursor.execute("SELECT DATABASE()")
                database = await cursor.fetchone()
                
                await cursor.execute("SELECT USER()")
                user = await cursor.fetchone()
                
                # Get database size
                size_query = """
                SELECT 
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size in MB'
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                """
                await cursor.execute(size_query)
                db_size = await cursor.fetchone()
                
                # Get connection count
                await cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                conn_count = await cursor.fetchone()
            
            conn.close()
            
            return {
                'server_info': {
                    'version': version[0] if version else 'Unknown',
                    'database': database[0] if database else 'Unknown',
                    'user': user[0] if user else 'Unknown',
                    'database_size_mb': db_size[0] if db_size else 0,
                    'active_connections': conn_count[1] if conn_count else 0
                },
                'connection_details': {
                    'host': params['host'],
                    'port': params['port'],
                    'charset': params.get('charset', 'utf8mb4'),
                    'ssl_mode': params.get('ssl_mode', 'preferred')
                },
                'capabilities': [
                    'foreign_keys', 'triggers', 'functions', 'views', 
                    'indexes', 'constraints', 'json', 'fulltext'
                ]
            }
            
        except Exception as e:
            raise Exception(f"MySQL connection failed: {str(e)}")
    
    async def _test_mongodb_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test MongoDB connection"""
        if not motor:
            raise ImportError("motor not installed. Install with: pip install motor")
        
        try:
            # Build connection string
            if params.get('username') and params.get('password'):
                conn_str = f"mongodb://{params['username']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
            else:
                conn_str = f"mongodb://{params['host']}:{params['port']}/{params['database']}"
            
            # Add auth source if specified
            if params.get('auth_source'):
                conn_str += f"?authSource={params['auth_source']}"
            
            # Create client
            client = motor.motor_asyncio.AsyncIOMotorClient(
                conn_str,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000
            )
            
            # Test connection
            await client.admin.command('ping')
            
            # Get server info
            server_info = await client.server_info()
            db_stats = await client[params['database']].command('dbStats')
            
            # Get collections
            collection_names = await client[params['database']].list_collection_names()
            
            client.close()
            
            return {
                'server_info': {
                    'version': server_info.get('version', 'Unknown'),
                    'database': params['database'],
                    'collections_count': len(collection_names),
                    'database_size_bytes': db_stats.get('dataSize', 0),
                    'storage_engine': server_info.get('storageEngines', ['Unknown'])[0]
                },
                'connection_details': {
                    'host': params['host'],
                    'port': params['port'],
                    'auth_source': params.get('auth_source', 'admin'),
                    'replica_set': params.get('replica_set')
                },
                'capabilities': [
                    'collections', 'indexes', 'aggregation_pipelines', 
                    'geospatial', 'text_search', 'transactions'
                ]
            }
            
        except Exception as e:
            raise Exception(f"MongoDB connection failed: {str(e)}")
    
    async def _test_sqlite_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test SQLite connection"""
        if not aiosqlite:
            raise ImportError("aiosqlite not installed. Install with: pip install aiosqlite")
        
        try:
            file_path = params['file_path']
            
            # Test connection
            async with aiosqlite.connect(file_path) as conn:
                # Get SQLite version
                cursor = await conn.execute("SELECT sqlite_version()")
                version = await cursor.fetchone()
                
                # Get database info
                cursor = await conn.execute("PRAGMA database_list")
                db_info = await cursor.fetchone()
                
                # Get table count
                cursor = await conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = await cursor.fetchone()
                
                # Get database size (if file exists)
                import os
                file_size = 0
                if file_path != ':memory:' and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
            
            return {
                'server_info': {
                    'version': version[0] if version else 'Unknown',
                    'database': params['database'],
                    'file_path': file_path,
                    'is_memory': params.get('is_memory', False),
                    'file_size_bytes': file_size,
                    'table_count': table_count[0] if table_count else 0
                },
                'connection_details': {
                    'file_path': file_path,
                    'is_memory': params.get('is_memory', False)
                },
                'capabilities': [
                    'foreign_keys', 'triggers', 'views', 'indexes', 
                    'constraints', 'json1', 'fts'
                ]
            }
            
        except Exception as e:
            raise Exception(f"SQLite connection failed: {str(e)}")
    
    async def _test_redis_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test Redis connection"""
        if not aioredis:
            raise ImportError("aioredis not installed. Install with: pip install aioredis")
        
        try:
            # Build connection URL
            if params.get('username') and params.get('password'):
                redis_url = f"redis://{params['username']}:{params['password']}@{params['host']}:{params['port']}/{params.get('db', 0)}"
            else:
                redis_url = f"redis://{params['host']}:{params['port']}/{params.get('db', 0)}"
            
            # Create connection
            redis = aioredis.from_url(redis_url, socket_timeout=30, socket_connect_timeout=30)
            
            # Test connection
            await redis.ping()
            
            # Get server info
            info = await redis.info()
            
            await redis.close()
            
            return {
                'server_info': {
                    'version': info.get('redis_version', 'Unknown'),
                    'database': params.get('db', 0),
                    'memory_usage_bytes': info.get('used_memory', 0),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                },
                'connection_details': {
                    'host': params['host'],
                    'port': params['port'],
                    'database': params.get('db', 0),
                    'ssl': params.get('ssl', False)
                },
                'capabilities': [
                    'key_value', 'pub_sub', 'transactions', 'lua_scripts', 
                    'persistence', 'clustering'
                ]
            }
            
        except Exception as e:
            raise Exception(f"Redis connection failed: {str(e)}")
    
    def _generate_connection_id(self, connection_url: str) -> str:
        """Generate unique connection ID from URL"""
        # Mask sensitive data and create hash
        masked_url = ConnectionURLParser.mask_sensitive_data(connection_url)
        return hashlib.md5(masked_url.encode()).hexdigest()[:12]
    
    def _get_troubleshooting_tips(self, error_message: str, db_type: str) -> List[str]:
        """Get troubleshooting tips based on error message and database type"""
        tips = []
        
        error_lower = error_message.lower()
        
        # Common connection issues
        if 'timeout' in error_lower or 'timed out' in error_lower:
            tips.extend([
                "Check if the database server is running and accessible",
                "Verify firewall settings and network connectivity",
                "Consider increasing connection timeout values"
            ])
        
        elif 'authentication' in error_lower or 'login' in error_lower or 'password' in error_lower:
            tips.extend([
                "Verify username and password are correct",
                "Check if user has permission to access the database",
                "Ensure authentication method is supported"
            ])
        
        elif 'connection refused' in error_lower or 'no route to host' in error_lower:
            tips.extend([
                "Verify the host address and port number",
                "Check if the database service is running",
                "Verify firewall and network configuration"
            ])
        
        elif 'database' in error_lower and 'not found' in error_lower:
            tips.extend([
                "Verify the database name is correct",
                "Check if the database exists on the server",
                "Ensure user has access to the specified database"
            ])
        
        # Database-specific tips
        if db_type == 'postgresql':
            tips.extend([
                "Check PostgreSQL server configuration (postgresql.conf)",
                "Verify pg_hba.conf for authentication settings",
                "Ensure the database is accepting connections"
            ])
        
        elif db_type == 'mysql':
            tips.extend([
                "Check MySQL server configuration",
                "Verify user privileges with GRANT statements",
                "Ensure MySQL is binding to the correct interface"
            ])
        
        elif db_type == 'mongodb':
            tips.extend([
                "Check MongoDB configuration and auth settings",
                "Verify replica set configuration if applicable",
                "Ensure MongoDB is accepting connections on the specified port"
            ])
        
        elif db_type == 'sqlite':
            tips.extend([
                "Verify the database file path is correct",
                "Check file permissions for the database file",
                "Ensure the directory exists and is writable"
            ])
        
        elif db_type == 'redis':
            tips.extend([
                "Check Redis configuration and authentication",
                "Verify Redis is running and accepting connections",
                "Check if the specified database number exists"
            ])
        
        # Default tips if no specific ones match
        if not tips:
            tips = [
                "Check database server status and configuration",
                "Verify connection parameters are correct",
                "Review database logs for additional error details"
            ]
        
        return tips
    
    async def get_connection_health(self, connection_id: str) -> Dict[str, Any]:
        """Get health status for a specific connection"""
        return self.health_status.get(connection_id, {
            'status': 'unknown',
            'message': 'Connection not found'
        })
    
    async def get_all_connections_health(self) -> Dict[str, Any]:
        """Get health status for all connections"""
        return {
            'connections': self.health_status,
            'summary': {
                'total_connections': len(self.health_status),
                'healthy_connections': len([c for c in self.health_status.values() if c.get('status') == 'healthy']),
                'error_connections': len([c for c in self.health_status.values() if c.get('status') == 'error']),
                'last_updated': datetime.now().isoformat()
            }
        }

# Global connection manager instance
connection_manager = DatabaseConnectionManager()
