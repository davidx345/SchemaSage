"""
PostgreSQL Database Handler
"""
from sqlalchemy import create_engine, text, inspect
from typing import Dict, Any
import pandas as pd

from .base_handler import DatabaseHandler
from models import DatabaseSchema, TableSchema, ColumnSchema


class PostgreSQLHandler(DatabaseHandler):
    """PostgreSQL database handler."""
    
    def connect(self) -> bool:
        try:
            connection_string = (
                f"postgresql://{self.connection.username}:{self.connection.password}"
                f"@{self.connection.host}:{self.connection.port}/{self.connection.database}"
            )
            self.engine = create_engine(connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None
    
    def test_connection(self) -> Dict[str, Any]:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()")).fetchone()
                return {
                    "status": "success",
                    "version": result[0] if result else "Unknown",
                    "database_type": "PostgreSQL"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "database_type": "PostgreSQL"
            }
    
    def extract_schema(self) -> DatabaseSchema:
        """Extract PostgreSQL schema."""
        inspector = inspect(self.engine)
        schema_info = DatabaseSchema(
            database_name=self.connection.database,
            tables=[]
        )
        
        # Get database version
        with self.engine.connect() as conn:
            version_result = conn.execute(text("SELECT version()")).fetchone()
            version = version_result[0] if version_result else "Unknown"
            schema_info.metadata["version"] = version
        
        # Get all tables
        table_names = inspector.get_table_names()
        
        for table_name in table_names:
            columns = []
            pg_columns = inspector.get_columns(table_name)
            
            for col in pg_columns:
                column_schema = ColumnSchema(
                    name=col['name'],
                    data_type=str(col['type']),
                    is_nullable=col['nullable'],
                    is_primary_key=False,  # Will be updated below
                    default_value=col.get('default'),
                    max_length=getattr(col['type'], 'length', None),
                    precision=getattr(col['type'], 'precision', None),
                    scale=getattr(col['type'], 'scale', None)
                )
                columns.append(column_schema)
            
            # Get primary keys
            pk_constraint = inspector.get_pk_constraint(table_name)
            if pk_constraint and pk_constraint['constrained_columns']:
                for col in columns:
                    if col.name in pk_constraint['constrained_columns']:
                        col.is_primary_key = True
            
            # Get indexes
            indexes = inspector.get_indexes(table_name)
            index_info = [
                {
                    "name": idx['name'],
                    "columns": idx['column_names'],
                    "unique": idx['unique']
                }
                for idx in indexes
            ]
            
            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys(table_name)
            fk_info = [
                {
                    "name": fk['name'],
                    "columns": fk['constrained_columns'],
                    "referenced_table": fk['referred_table'],
                    "referenced_columns": fk['referred_columns']
                }
                for fk in foreign_keys
            ]
            
            table_schema = TableSchema(
                name=table_name,
                columns=columns,
                indexes=index_info,
                foreign_keys=fk_info,
                row_count=self._get_row_count(table_name)
            )
            schema_info.tables.append(table_schema)
        
        return schema_info
    
    def get_table_data_sample(self, table_name: str, limit: int = 100) -> pd.DataFrame:
        """Get sample data from PostgreSQL table."""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return pd.read_sql(query, self.engine)
    
    def execute_query(self, query: str) -> Any:
        """Execute query on PostgreSQL."""
        with self.engine.connect() as conn:
            return conn.execute(text(query))
