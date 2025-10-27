"""
Database integration implementations
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
import pymongo
import redis
import time

from .base import BaseIntegration, IntegrationConfig, IntegrationType, AuthenticationType
from models.schemas import SchemaResponse, TableInfo, ColumnInfo, Relationship

logger = logging.getLogger(__name__)

class DatabaseIntegration(BaseIntegration):
    """Integration for relational databases"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.engine: Optional[Engine] = None
    
    async def connect(self) -> bool:
        """Establish database connection"""
        try:
            connection_string = self._build_connection_string()
            # ✅ TRANSACTION POOLER CONFIGURATION
            # Using NullPool for external database connections
            from sqlalchemy.pool import NullPool
            self.engine = create_engine(
                connection_string,
                poolclass=NullPool,  # No pooling for external connections
                pool_pre_ping=True,
                connect_args={
                    "connect_timeout": 10,
                    "options": "-c statement_timeout=30000"
                }
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.is_connected = True
            logger.info(f"Connected to database: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection"""
        start_time = time.time()
        
        try:
            if not self.engine:
                await self.connect()
            
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            response_time = time.time() - start_time
            self.update_metrics(True, response_time)
            
            return {
                "success": True,
                "message": "Database connection successful",
                "response_time": response_time,
                "database_type": self._get_database_type()
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"Database connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def get_schema(self) -> Optional[SchemaResponse]:
        """Extract schema information from database"""
        try:
            if not self.engine:
                await self.connect()
            
            inspector = inspect(self.engine)
            
            # Get tables
            table_names = inspector.get_table_names()
            tables = []
            
            for table_name in table_names:
                columns = self._get_table_columns(inspector, table_name)
                
                table_info = TableInfo(
                    name=table_name,
                    columns=columns,
                    indexes=self._get_table_indexes(inspector, table_name),
                    constraints=self._get_table_constraints(inspector, table_name)
                )
                tables.append(table_info)
            
            # Get relationships
            relationships = self._get_relationships(inspector, table_names)
            
            return SchemaResponse(
                schema_name=self.config.settings.get("database_name", "default"),
                tables=tables,
                relationships=relationships,
                metadata={
                    "database_type": self._get_database_type(),
                    "total_tables": len(tables),
                    "extraction_time": time.time()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract schema from {self.config.name}: {str(e)}")
            return None
    
    def _build_connection_string(self) -> str:
        """Build database connection string"""
        creds = self.config.credentials.credentials
        settings = self.config.settings
        
        db_type = settings.get("database_type", "postgresql")
        host = settings.get("host", "localhost")
        port = settings.get("port", 5432)
        database = settings.get("database_name", "postgres")
        
        if self.config.credentials.auth_type == AuthenticationType.BASIC_AUTH:
            username = creds.get("username")
            password = creds.get("password")
            return f"{db_type}://{username}:{password}@{host}:{port}/{database}"
        
        # Add other auth types as needed
        return f"{db_type}://{host}:{port}/{database}"
    
    def _get_database_type(self) -> str:
        """Get database type from engine"""
        if self.engine:
            return self.engine.dialect.name
        return self.config.settings.get("database_type", "unknown")
    
    def _get_table_columns(self, inspector, table_name: str) -> List[ColumnInfo]:
        """Get column information for a table"""
        columns = []
        
        for col in inspector.get_columns(table_name):
            column_info = ColumnInfo(
                name=col["name"],
                type=str(col["type"]),
                nullable=col.get("nullable", True),
                primary_key=col.get("primary_key", False),
                foreign_key=col.get("foreign_key"),
                default=col.get("default"),
                comment=col.get("comment")
            )
            columns.append(column_info)
        
        return columns
    
    def _get_table_indexes(self, inspector, table_name: str) -> List[Dict[str, Any]]:
        """Get index information for a table"""
        try:
            indexes = inspector.get_indexes(table_name)
            return [
                {
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx.get("unique", False)
                }
                for idx in indexes
            ]
        except:
            return []
    
    def _get_table_constraints(self, inspector, table_name: str) -> List[Dict[str, Any]]:
        """Get constraint information for a table"""
        constraints = []
        
        try:
            # Primary key constraints
            pk = inspector.get_pk_constraint(table_name)
            if pk and pk["constrained_columns"]:
                constraints.append({
                    "type": "primary_key",
                    "name": pk.get("name", "pk_" + table_name),
                    "columns": pk["constrained_columns"]
                })
            
            # Foreign key constraints
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                constraints.append({
                    "type": "foreign_key",
                    "name": fk.get("name", "fk_" + table_name),
                    "columns": fk["constrained_columns"],
                    "referenced_table": fk["referred_table"],
                    "referenced_columns": fk["referred_columns"]
                })
        except:
            pass
        
        return constraints
    
    def _get_relationships(self, inspector, table_names: List[str]) -> List[Relationship]:
        """Extract relationships between tables"""
        relationships = []
        
        for table_name in table_names:
            try:
                fks = inspector.get_foreign_keys(table_name)
                
                for fk in fks:
                    relationship = Relationship(
                        source_table=table_name,
                        target_table=fk["referred_table"],
                        source_column=fk["constrained_columns"][0] if fk["constrained_columns"] else "",
                        target_column=fk["referred_columns"][0] if fk["referred_columns"] else "",
                        relationship_type="one_to_many"  # Default assumption
                    )
                    relationships.append(relationship)
            except:
                continue
        
        return relationships

class MongoDBIntegration(BaseIntegration):
    """Integration for MongoDB"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.client: Optional[pymongo.MongoClient] = None
        self.database = None
    
    async def connect(self) -> bool:
        """Establish MongoDB connection"""
        try:
            connection_string = self._build_connection_string()
            self.client = pymongo.MongoClient(connection_string)
            
            # Test connection
            self.client.admin.command('ping')
            
            database_name = self.config.settings.get("database_name", "test")
            self.database = self.client[database_name]
            
            self.is_connected = True
            logger.info(f"Connected to MongoDB: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test MongoDB connection"""
        start_time = time.time()
        
        try:
            if not self.client:
                await self.connect()
            
            self.client.admin.command('ping')
            
            response_time = time.time() - start_time
            self.update_metrics(True, response_time)
            
            return {
                "success": True,
                "message": "MongoDB connection successful",
                "response_time": response_time,
                "server_info": self.client.server_info()
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"MongoDB connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def get_schema(self) -> Optional[SchemaResponse]:
        """Extract schema information from MongoDB"""
        try:
            if not self.database:
                await self.connect()
            
            collection_names = self.database.list_collection_names()
            tables = []
            
            for collection_name in collection_names:
                collection = self.database[collection_name]
                
                # Sample documents to infer schema
                sample_docs = list(collection.find().limit(100))
                columns = self._infer_columns_from_documents(sample_docs)
                
                table_info = TableInfo(
                    name=collection_name,
                    columns=columns,
                    indexes=self._get_collection_indexes(collection),
                    constraints=[]
                )
                tables.append(table_info)
            
            return SchemaResponse(
                schema_name=self.database.name,
                tables=tables,
                relationships=[],  # MongoDB doesn't have explicit relationships
                metadata={
                    "database_type": "mongodb",
                    "total_collections": len(tables),
                    "extraction_time": time.time()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract schema from MongoDB {self.config.name}: {str(e)}")
            return None
    
    def _build_connection_string(self) -> str:
        """Build MongoDB connection string"""
        creds = self.config.credentials.credentials
        settings = self.config.settings
        
        host = settings.get("host", "localhost")
        port = settings.get("port", 27017)
        
        if self.config.credentials.auth_type == AuthenticationType.BASIC_AUTH:
            username = creds.get("username")
            password = creds.get("password")
            return f"mongodb://{username}:{password}@{host}:{port}"
        
        return f"mongodb://{host}:{port}"
    
    def _infer_columns_from_documents(self, documents: List[Dict]) -> List[ColumnInfo]:
        """Infer column structure from MongoDB documents"""
        if not documents:
            return []
        
        # Collect all unique fields and their types
        field_types = {}
        
        for doc in documents:
            for field, value in doc.items():
                if field not in field_types:
                    field_types[field] = set()
                
                field_types[field].add(type(value).__name__)
        
        columns = []
        for field, types in field_types.items():
            # Use most common type or 'mixed' if multiple types
            field_type = list(types)[0] if len(types) == 1 else "mixed"
            
            column_info = ColumnInfo(
                name=field,
                type=field_type,
                nullable=True,  # MongoDB fields are generally nullable
                primary_key=(field == "_id")
            )
            columns.append(column_info)
        
        return columns
    
    def _get_collection_indexes(self, collection) -> List[Dict[str, Any]]:
        """Get index information for a MongoDB collection"""
        try:
            indexes = []
            for index in collection.list_indexes():
                indexes.append({
                    "name": index.get("name"),
                    "keys": list(index.get("key", {}).keys()),
                    "unique": index.get("unique", False)
                })
            return indexes
        except:
            return []

class RedisIntegration(BaseIntegration):
    """Integration for Redis"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.client: Optional[redis.Redis] = None
    
    async def connect(self) -> bool:
        """Establish Redis connection"""
        try:
            host = self.config.settings.get("host", "localhost")
            port = self.config.settings.get("port", 6379)
            db = self.config.settings.get("database", 0)
            
            if self.config.credentials.auth_type == AuthenticationType.BASIC_AUTH:
                password = self.config.credentials.credentials.get("password")
                self.client = redis.Redis(host=host, port=port, db=db, password=password)
            else:
                self.client = redis.Redis(host=host, port=port, db=db)
            
            # Test connection
            self.client.ping()
            
            self.is_connected = True
            logger.info(f"Connected to Redis: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            self.client = None
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Redis connection"""
        start_time = time.time()
        
        try:
            if not self.client:
                await self.connect()
            
            self.client.ping()
            
            response_time = time.time() - start_time
            self.update_metrics(True, response_time)
            
            return {
                "success": True,
                "message": "Redis connection successful",
                "response_time": response_time,
                "server_info": self.client.info()
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"Redis connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def get_schema(self) -> Optional[SchemaResponse]:
        """Extract schema information from Redis"""
        try:
            if not self.client:
                await self.connect()
            
            # Redis doesn't have a traditional schema, but we can analyze key patterns
            key_patterns = self._analyze_key_patterns()
            
            tables = []
            for pattern, info in key_patterns.items():
                table_info = TableInfo(
                    name=pattern,
                    columns=[
                        ColumnInfo(
                            name="key",
                            type="string",
                            primary_key=True
                        ),
                        ColumnInfo(
                            name="value",
                            type=info["value_type"],
                            nullable=False
                        )
                    ],
                    indexes=[],
                    constraints=[]
                )
                tables.append(table_info)
            
            return SchemaResponse(
                schema_name="redis",
                tables=tables,
                relationships=[],
                metadata={
                    "database_type": "redis",
                    "total_patterns": len(key_patterns),
                    "extraction_time": time.time()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract schema from Redis {self.config.name}: {str(e)}")
            return None
    
    def _analyze_key_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze Redis key patterns to infer structure"""
        try:
            keys = self.client.keys("*")
            patterns = {}
            
            for key in keys[:100]:  # Limit analysis to first 100 keys
                key_str = key.decode() if isinstance(key, bytes) else str(key)
                
                # Simple pattern extraction (could be more sophisticated)
                pattern = self._extract_pattern(key_str)
                
                if pattern not in patterns:
                    patterns[pattern] = {
                        "count": 0,
                        "value_type": "unknown",
                        "sample_keys": []
                    }
                
                patterns[pattern]["count"] += 1
                patterns[pattern]["sample_keys"].append(key_str)
                
                # Determine value type
                try:
                    value_type = self.client.type(key).decode()
                    patterns[pattern]["value_type"] = value_type
                except:
                    pass
            
            return patterns
        except:
            return {}
