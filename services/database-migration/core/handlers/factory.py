"""
Database Handler Factory
"""
from typing import Dict, Type

from .base_handler import DatabaseHandler
from .postgresql_handler import PostgreSQLHandler
from .mysql_handler import MySQLHandler
from .sqlite_handler import SQLiteHandler
from .mongodb_handler import MongoDBHandler
from ...models import DatabaseConnection


def get_database_handler(connection: DatabaseConnection) -> DatabaseHandler:
    """Factory function to create appropriate database handler."""
    handlers: Dict[str, Type[DatabaseHandler]] = {
        "postgresql": PostgreSQLHandler,
        "mysql": MySQLHandler,
        "sqlite": SQLiteHandler,
        "mongodb": MongoDBHandler,
    }
    
    handler_class = handlers.get(connection.database_type.lower())
    if not handler_class:
        raise ValueError(f"Unsupported database type: {connection.database_type}")
    
    return handler_class(connection)
