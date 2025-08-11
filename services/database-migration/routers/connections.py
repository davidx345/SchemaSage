"""
Database Connections Router
Database connection management, testing, and schema analysis
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import uuid
import logging

from ..models import DatabaseConnection, SchemaInfo, ConnectionTest, SchemaComparison
from ..core.handlers import get_database_handler
from ..core.intelligence import MigrationIntelligence

router = APIRouter(prefix="/connections", tags=["connections"])
logger = logging.getLogger(__name__)

# External dependencies (these would be injected in production)
connections_store: Dict[str, DatabaseConnection] = {}

# Initialize services
intelligence = MigrationIntelligence()

@router.post("", response_model=Dict[str, Any])
async def create_connection(connection: DatabaseConnection):
    """Create a new database connection."""
    try:
        connection_id = str(uuid.uuid4())
        connection.connection_id = connection_id
        
        # Test the connection
        handler = get_database_handler(connection)
        is_connected = handler.connect()
        
        if not is_connected:
            raise HTTPException(status_code=400, detail="Failed to connect to database")
        
        # Test connection and get info
        test_result = handler.test_connection()
        handler.disconnect()
        
        # Store connection
        connections_store[connection_id] = connection
        
        return {
            "connection_id": connection_id,
            "status": "connected",
            "database_info": test_result,
            "message": "Database connection created successfully"
        }
    
    except Exception as e:
        logger.error(f"Error creating connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[Dict[str, Any]])
async def list_connections():
    """List all database connections."""
    connections_list = []
    for conn_id, connection in connections_store.items():
        connections_list.append({
            "connection_id": conn_id,
            "name": connection.name,
            "database_type": connection.database_type,
            "host": connection.host,
            "database": connection.database,
            "created_at": connection.created_at
        })
    return connections_list

@router.get("/{connection_id}", response_model=DatabaseConnection)
async def get_connection(connection_id: str):
    """Get a specific database connection."""
    if connection_id not in connections_store:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connections_store[connection_id]

@router.post("/{connection_id}/test", response_model=ConnectionTest)
async def test_connection(connection_id: str):
    """Test a database connection."""
    if connection_id not in connections_store:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        connection = connections_store[connection_id]
        handler = get_database_handler(connection)
        
        is_connected = handler.connect()
        if is_connected:
            test_result = handler.test_connection()
            handler.disconnect()
            
            return ConnectionTest(
                connection_id=connection_id,
                status="success",
                message="Connection successful",
                details=test_result
            )
        else:
            return ConnectionTest(
                connection_id=connection_id,
                status="failed",
                message="Failed to connect to database",
                details={}
            )
    
    except Exception as e:
        logger.error(f"Error testing connection {connection_id}: {e}")
        return ConnectionTest(
            connection_id=connection_id,
            status="error",
            message=str(e),
            details={}
        )

@router.delete("/{connection_id}")
async def delete_connection(connection_id: str):
    """Delete a database connection."""
    if connection_id not in connections_store:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    del connections_store[connection_id]
    return {"message": "Connection deleted successfully"}

@router.post("/{connection_id}/analyze", response_model=SchemaInfo)
async def analyze_schema(connection_id: str):
    """Analyze database schema."""
    if connection_id not in connections_store:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        connection = connections_store[connection_id]
        handler = get_database_handler(connection)
        
        if not handler.connect():
            raise HTTPException(status_code=400, detail="Failed to connect to database")
        
        schema_info = handler.extract_schema()
        handler.disconnect()
        
        return schema_info
    
    except Exception as e:
        logger.error(f"Error analyzing schema for connection {connection_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare", response_model=SchemaComparison)
async def compare_schemas(source_connection_id: str, target_connection_id: str):
    """Compare two database schemas."""
    if source_connection_id not in connections_store:
        raise HTTPException(status_code=404, detail="Source connection not found")
    if target_connection_id not in connections_store:
        raise HTTPException(status_code=404, detail="Target connection not found")
    
    try:
        # Get source schema
        source_connection = connections_store[source_connection_id]
        source_handler = get_database_handler(source_connection)
        source_handler.connect()
        source_schema = source_handler.extract_schema()
        source_handler.disconnect()
        
        # Get target schema
        target_connection = connections_store[target_connection_id]
        target_handler = get_database_handler(target_connection)
        target_handler.connect()
        target_schema = target_handler.extract_schema()
        target_handler.disconnect()
        
        # Compare schemas using intelligence engine
        comparison = intelligence.compare_schemas(source_schema, target_schema)
        
        return comparison
    
    except Exception as e:
        logger.error(f"Error comparing schemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
