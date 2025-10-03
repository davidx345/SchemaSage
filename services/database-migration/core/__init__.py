"""
Core module initialization
"""
from .handlers import get_database_handler, DatabaseHandler, PostgreSQLHandler, MySQLHandler, SQLiteHandler, MongoDBHandler
# Temporarily disabled due to missing model dependencies
# from .intelligence import MigrationIntelligence

__all__ = [
    'get_database_handler',
    'DatabaseHandler', 
    'PostgreSQLHandler',
    'MySQLHandler', 
    'SQLiteHandler',
    'MongoDBHandler',
    # 'MigrationIntelligence'
]
