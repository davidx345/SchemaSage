"""
MongoDB Database Handler
"""
import pymongo
from typing import Dict, List, Any
import pandas as pd

from .base_handler import DatabaseHandler
from ...models import SchemaInfo, TableSchema, ColumnSchema


class MongoDBHandler(DatabaseHandler):
    """MongoDB database handler."""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.client = None
        self.db = None
    
    def connect(self) -> bool:
        try:
            if self.connection.username and self.connection.password:
                connection_string = (
                    f"mongodb://{self.connection.username}:{self.connection.password}"
                    f"@{self.connection.host}:{self.connection.port}/{self.connection.database}"
                )
            else:
                connection_string = f"mongodb://{self.connection.host}:{self.connection.port}"
            
            self.client = pymongo.MongoClient(connection_string)
            self.db = self.client[self.connection.database]
            # Test connection
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
    
    def test_connection(self) -> Dict[str, Any]:
        try:
            server_info = self.client.server_info()
            return {
                "status": "success",
                "version": server_info.get("version", "Unknown"),
                "database_type": "MongoDB"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "database_type": "MongoDB"
            }
    
    def extract_schema(self) -> SchemaInfo:
        """Extract MongoDB schema by analyzing documents."""
        schema_info = SchemaInfo(
            database_name=self.connection.database,
            database_type=self.connection.database_type,
            version="",
            tables=[]  # Collections in MongoDB
        )
        
        # Get MongoDB version
        server_info = self.client.server_info()
        schema_info.version = server_info.get("version", "Unknown")
        
        # Get all collections
        collection_names = self.db.list_collection_names()
        
        for collection_name in collection_names:
            collection = self.db[collection_name]
            
            # Sample documents to infer schema
            sample_docs = list(collection.find().limit(100))
            columns = self._infer_schema_from_documents(sample_docs)
            
            table_schema = TableSchema(
                name=collection_name,
                columns=columns,
                indexes=[],
                foreign_keys=[],
                row_count=collection.count_documents({})
            )
            schema_info.tables.append(table_schema)
        
        return schema_info
    
    def _infer_schema_from_documents(self, documents: List[Dict]) -> List[ColumnSchema]:
        """Infer schema from MongoDB documents."""
        field_types = {}
        
        for doc in documents:
            self._analyze_document(doc, field_types)
        
        columns = []
        for field_name, type_info in field_types.items():
            most_common_type = max(type_info, key=type_info.get)
            
            column_schema = ColumnSchema(
                name=field_name,
                data_type=most_common_type,
                is_nullable=True,  # MongoDB fields are generally nullable
                is_primary_key=(field_name == "_id"),
                default_value=None,
                max_length=None,
                precision=None,
                scale=None
            )
            columns.append(column_schema)
        
        return columns
    
    def _analyze_document(self, doc: Dict, field_types: Dict, prefix: str = ""):
        """Recursively analyze document structure."""
        for key, value in doc.items():
            field_name = f"{prefix}.{key}" if prefix else key
            
            if field_name not in field_types:
                field_types[field_name] = {}
            
            value_type = type(value).__name__
            if value_type in field_types[field_name]:
                field_types[field_name][value_type] += 1
            else:
                field_types[field_name][value_type] = 1
    
    def get_table_data_sample(self, table_name: str, limit: int = 100) -> pd.DataFrame:
        """Get sample data from MongoDB collection."""
        collection = self.db[table_name]
        documents = list(collection.find().limit(limit))
        return pd.DataFrame(documents)
    
    def execute_query(self, query: str) -> Any:
        """Execute query on MongoDB (limited support)."""
        # MongoDB doesn't use SQL, so this would need to be adapted
        # for MongoDB query syntax or aggregation pipelines
        raise NotImplementedError("MongoDB query execution requires different syntax")
