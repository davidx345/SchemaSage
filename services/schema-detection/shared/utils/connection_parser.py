"""
Universal Database Connection URL Parser
Handles parsing and validation of connection URLs for all supported database types
"""
import re
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)

class ConnectionURLParser:
    """Parse and validate database connection URLs"""
    
    SUPPORTED_SCHEMES = {
        'postgresql': {'default_port': 5432, 'aliases': ['postgres']},
        'mysql': {'default_port': 3306, 'aliases': ['mariadb']},
        'mongodb': {'default_port': 27017, 'aliases': ['mongo']},
        'sqlite': {'default_port': None, 'aliases': []},
        'redis': {'default_port': 6379, 'aliases': []}
    }
    
    @classmethod
    def parse_connection_url(cls, connection_url: str) -> Dict[str, Any]:
        """
        Parse a database connection URL into components
        
        Args:
            connection_url: Database connection URL
            
        Returns:
            Dictionary with parsed connection parameters
            
        Raises:
            ValueError: If URL format is invalid or unsupported
        """
        if not connection_url or not connection_url.strip():
            raise ValueError("Connection URL cannot be empty")
        
        try:
            parsed = urlparse(connection_url)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {str(e)}")
        
        # Normalize scheme
        scheme = parsed.scheme.lower()
        db_type = cls._normalize_scheme(scheme)
        
        if db_type not in cls.SUPPORTED_SCHEMES:
            raise ValueError(f"Unsupported database type: {scheme}")
        
        # Handle SQLite special case
        if db_type == 'sqlite':
            return cls._parse_sqlite_url(connection_url, parsed)
        
        # Parse standard URL components
        connection_params = {
            'database_type': db_type,
            'scheme': scheme,
            'host': parsed.hostname,
            'port': parsed.port or cls.SUPPORTED_SCHEMES[db_type]['default_port'],
            'username': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/') if parsed.path else None,
            'query_params': parse_qs(parsed.query),
            'original_url': connection_url
        }
        
        # Validate required fields
        cls._validate_connection_params(connection_params, db_type)
        
        # Parse database-specific options
        connection_params.update(cls._parse_db_specific_options(connection_params, db_type))
        
        return connection_params
    
    @classmethod
    def _normalize_scheme(cls, scheme: str) -> str:
        """Normalize database scheme to standard type"""
        for db_type, config in cls.SUPPORTED_SCHEMES.items():
            if scheme == db_type or scheme in config['aliases']:
                return db_type
        return scheme
    
    @classmethod
    def _parse_sqlite_url(cls, url: str, parsed) -> Dict[str, Any]:
        """Parse SQLite connection URL"""
        # SQLite URLs: sqlite:///path/to/file.db or sqlite:///:memory:
        path = parsed.path
        if not path:
            raise ValueError("SQLite URL must include database file path")
        
        return {
            'database_type': 'sqlite',
            'scheme': 'sqlite',
            'file_path': path,
            'database': path.split('/')[-1] if path != ':memory:' else ':memory:',
            'is_memory': path == ':memory:',
            'query_params': parse_qs(parsed.query),
            'original_url': url,
            'host': None,
            'port': None,
            'username': None,
            'password': None
        }
    
    @classmethod
    def _validate_connection_params(cls, params: Dict[str, Any], db_type: str) -> None:
        """Validate required connection parameters"""
        if db_type == 'sqlite':
            if not params.get('file_path'):
                raise ValueError("SQLite requires file_path")
            return
        
        # Validate required fields for network databases
        required_fields = ['host']
        if db_type in ['postgresql', 'mysql', 'mongodb']:
            required_fields.extend(['username', 'database'])
        
        missing_fields = [field for field in required_fields if not params.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate port
        if params.get('port'):
            try:
                port = int(params['port'])
                if not (1 <= port <= 65535):
                    raise ValueError("Port must be between 1 and 65535")
                params['port'] = port
            except (ValueError, TypeError):
                raise ValueError("Port must be a valid integer")
    
    @classmethod
    def _parse_db_specific_options(cls, params: Dict[str, Any], db_type: str) -> Dict[str, Any]:
        """Parse database-specific connection options"""
        query_params = params.get('query_params', {})
        options = {}
        
        if db_type == 'postgresql':
            options.update({
                'ssl_mode': query_params.get('ssl', ['prefer'])[0],
                'connect_timeout': int(query_params.get('connect_timeout', [30])[0]),
                'application_name': query_params.get('application_name', ['SchemaSage'])[0],
                'schema': query_params.get('schema', ['public'])[0]
            })
        
        elif db_type == 'mysql':
            options.update({
                'charset': query_params.get('charset', ['utf8mb4'])[0],
                'connect_timeout': int(query_params.get('connect_timeout', [30])[0]),
                'ssl_mode': query_params.get('ssl', ['preferred'])[0],
                'autocommit': query_params.get('autocommit', ['true'])[0].lower() == 'true'
            })
        
        elif db_type == 'mongodb':
            options.update({
                'auth_source': query_params.get('authSource', ['admin'])[0],
                'replica_set': query_params.get('replicaSet', [None])[0],
                'ssl': query_params.get('ssl', ['false'])[0].lower() == 'true',
                'connect_timeout_ms': int(query_params.get('connectTimeoutMS', [30000])[0]),
                'server_selection_timeout_ms': int(query_params.get('serverSelectionTimeoutMS', [30000])[0])
            })
        
        elif db_type == 'redis':
            options.update({
                'db': int(query_params.get('db', [0])[0]),
                'connect_timeout': int(query_params.get('connect_timeout', [30])[0]),
                'socket_timeout': int(query_params.get('socket_timeout', [30])[0]),
                'ssl': query_params.get('ssl', ['false'])[0].lower() == 'true'
            })
        
        return options
    
    @classmethod
    def build_connection_url(cls, params: Dict[str, Any]) -> str:
        """Build connection URL from parameters"""
        db_type = params.get('database_type')
        if not db_type:
            raise ValueError("database_type is required")
        
        if db_type == 'sqlite':
            path = params.get('file_path', '')
            query_string = cls._build_query_string(params.get('query_params', {}))
            return f"sqlite://{path}{query_string}"
        
        # Build standard URL
        scheme = params.get('scheme', db_type)
        username = params.get('username', '')
        password = params.get('password', '')
        host = params.get('host', 'localhost')
        port = params.get('port', cls.SUPPORTED_SCHEMES[db_type]['default_port'])
        database = params.get('database', '')
        
        # Build auth part
        auth_part = ''
        if username:
            auth_part = username
            if password:
                auth_part += f":{password}"
            auth_part += '@'
        
        # Build URL
        url = f"{scheme}://{auth_part}{host}"
        if port and port != cls.SUPPORTED_SCHEMES[db_type]['default_port']:
            url += f":{port}"
        
        if database:
            url += f"/{database}"
        
        # Add query parameters
        query_string = cls._build_query_string(params.get('query_params', {}))
        url += query_string
        
        return url
    
    @classmethod
    def _build_query_string(cls, query_params: Dict[str, Any]) -> str:
        """Build query string from parameters"""
        if not query_params:
            return ''
        
        query_parts = []
        for key, value in query_params.items():
            if isinstance(value, list) and value:
                value = value[0]
            if value is not None:
                query_parts.append(f"{key}={value}")
        
        return f"?{'&'.join(query_parts)}" if query_parts else ''
    
    @classmethod
    def mask_sensitive_data(cls, connection_url: str) -> str:
        """Mask password in connection URL for logging"""
        try:
            parsed = urlparse(connection_url)
            if parsed.password:
                masked_url = connection_url.replace(parsed.password, '***')
                return masked_url
            return connection_url
        except Exception:
            return "***masked_url***"
    
    @classmethod
    def validate_connection_url(cls, connection_url: str) -> Tuple[bool, str]:
        """
        Validate connection URL format
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            cls.parse_connection_url(connection_url)
            return True, ""
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    @classmethod
    def get_supported_schemes(cls) -> Dict[str, Any]:
        """Get information about supported database schemes"""
        return {
            scheme: {
                'default_port': config['default_port'],
                'aliases': config['aliases'],
                'example_urls': cls._get_example_urls(scheme)
            }
            for scheme, config in cls.SUPPORTED_SCHEMES.items()
        }
    
    @classmethod
    def _get_example_urls(cls, db_type: str) -> Dict[str, str]:
        """Get example URLs for each database type"""
        examples = {
            'postgresql': {
                'basic': 'postgresql://username:password@localhost:5432/database',
                'with_ssl': 'postgresql://username:password@host:5432/db?ssl=require',
                'with_options': 'postgresql://user:pass@host:5432/db?ssl=prefer&application_name=SchemaSage'
            },
            'mysql': {
                'basic': 'mysql://username:password@localhost:3306/database',
                'with_ssl': 'mysql://username:password@host:3306/db?ssl=required',
                'with_charset': 'mysql://user:pass@host:3306/db?charset=utf8mb4&ssl=preferred'
            },
            'mongodb': {
                'basic': 'mongodb://username:password@localhost:27017/database',
                'with_auth': 'mongodb://user:pass@host:27017/db?authSource=admin',
                'replica_set': 'mongodb://user:pass@host1:27017,host2:27017/db?replicaSet=rs0'
            },
            'sqlite': {
                'file': 'sqlite:///path/to/database.db',
                'absolute': 'sqlite:////absolute/path/to/database.db',
                'memory': 'sqlite://:memory:'
            },
            'redis': {
                'basic': 'redis://localhost:6379/0',
                'with_auth': 'redis://username:password@localhost:6379/0',
                'with_ssl': 'redis://user:pass@host:6379/0?ssl=true'
            }
        }
        
        return examples.get(db_type, {})
