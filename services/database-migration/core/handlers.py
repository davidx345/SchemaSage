"""
Database Connection Handlers - Modularized
Database connectivity and schema extraction handlers for multiple database types.
"""

# Import all handlers from modular structure
from .handlers.base_handler import DatabaseHandler
from .handlers.postgresql_handler import PostgreSQLHandler
from .handlers.mysql_handler import MySQLHandler
from .handlers.sqlite_handler import SQLiteHandler
from .handlers.mongodb_handler import MongoDBHandler
from .handlers.factory import get_database_handler

# Export classes for backward compatibility
__all__ = [
    'DatabaseHandler',
    'PostgreSQLHandler',
    'MySQLHandler',
    'SQLiteHandler',
    'MongoDBHandler',
    'get_database_handler'
]
