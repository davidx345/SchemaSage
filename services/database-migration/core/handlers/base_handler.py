"""
Abstract Base Database Handler
"""
from abc import ABC, abstractmethod
from sqlalchemy.engine import Engine
from typing import Dict, List, Any, Optional
import pandas as pd

from models import DatabaseConnection, SchemaInfo


class DatabaseHandler(ABC):
    """Abstract base class for database handlers."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.engine: Optional[Engine] = None
        self._metadata = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close database connection."""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test database connectivity."""
        pass
    
    @abstractmethod
    def extract_schema(self) -> SchemaInfo:
        """Extract complete schema information."""
        pass
    
    @abstractmethod
    def get_table_data_sample(self, table_name: str, limit: int = 100) -> pd.DataFrame:
        """Get sample data from table."""
        pass
    
    @abstractmethod
    def execute_query(self, query: str) -> Any:
        """Execute a query."""
        pass
    
    def _get_row_count(self, table_name: str) -> int:
        """Get row count for a table. Override in subclasses if needed."""
        try:
            if hasattr(self, 'engine') and self.engine:
                from sqlalchemy import text
                with self.engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
                    return result[0] if result else 0
        except:
            pass
        return 0
