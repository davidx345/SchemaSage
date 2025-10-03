"""
SQLite Database Handler
"""
from sqlalchemy import create_engine, text, inspect
from typing import Dict, Any
import pandas as pd

from .base_handler import DatabaseHandler
from models import DatabaseSchema, TableSchema, ColumnSchema


class SQLiteHandler(DatabaseHandler):
    """SQLite database handler."""
    
    def connect(self) -> bool:
        try:
            # host contains file path for SQLite
            connection_string = f"sqlite:///{self.connection.host}"
            self.engine = create_engine(connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"SQLite connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None
    
    def test_connection(self) -> Dict[str, Any]:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT sqlite_version()")).fetchone()
                return {
                    "status": "success",
                    "version": result[0] if result else "Unknown",
                    "database_type": "SQLite"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "database_type": "SQLite"
            }
    
    def extract_schema(self) -> DatabaseSchema:
        """Extract SQLite schema."""
        inspector = inspect(self.engine)
        schema_info = DatabaseSchema(
            database_name=self.connection.database or "main",
            tables=[]
        )
        
        # Get SQLite version
        with self.engine.connect() as conn:
            version_result = conn.execute(text("SELECT sqlite_version()")).fetchone()
            version = version_result[0] if version_result else "Unknown"
            schema_info.metadata["version"] = version
        
        table_names = inspector.get_table_names()
        
        for table_name in table_names:
            columns = []
            sqlite_columns = inspector.get_columns(table_name)
            
            for col in sqlite_columns:
                column_schema = ColumnSchema(
                    name=col['name'],
                    data_type=str(col['type']),
                    is_nullable=col['nullable'],
                    is_primary_key=col.get('primary_key', False),
                    default_value=col.get('default'),
                    max_length=None,  # SQLite doesn't enforce length
                    precision=None,
                    scale=None
                )
                columns.append(column_schema)
            
            table_schema = TableSchema(
                name=table_name,
                columns=columns,
                indexes=[],
                foreign_keys=[],
                row_count=self._get_row_count(table_name)
            )
            schema_info.tables.append(table_schema)
        
        return schema_info
    
    def get_table_data_sample(self, table_name: str, limit: int = 100) -> pd.DataFrame:
        """Get sample data from SQLite table."""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return pd.read_sql(query, self.engine)
    
    def execute_query(self, query: str) -> Any:
        """Execute query on SQLite."""
        with self.engine.connect() as conn:
            return conn.execute(text(query))
