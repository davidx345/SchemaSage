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
from ..core.connection_store import get_connection_store

router = APIRouter(prefix="/connections", tags=["connections"])
logger = logging.getLogger(__name__)

# Initialize services
intelligence = MigrationIntelligence()
store = get_connection_store()

@router.post("", response_model=Dict[str, Any])
async def create_connection(connection: DatabaseConnection):
    """Create a new database connection."""
    try:
        # Test the connection first
        handler = get_database_handler(connection)
        is_connected = handler.connect()
        
        if not is_connected:
            raise HTTPException(status_code=400, detail="Failed to connect to database")
        
        # Test connection and get info
        test_result = handler.test_connection()
        handler.disconnect()
        
        # Save connection to persistent storage
        connection_id = await store.save_connection(connection)
        
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
    return await store.list_connections()

@router.get("/{connection_id}", response_model=DatabaseConnection)
async def get_connection(connection_id: str):
    """Get a specific database connection."""
    connection = await store.get_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection

@router.post("/{connection_id}/test", response_model=ConnectionTest)
async def test_connection(connection_id: str):
    """Test a database connection."""
    connection = await store.get_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
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
    deleted = await store.delete_connection(connection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return {"message": "Connection deleted successfully"}

@router.post("/{connection_id}/analyze", response_model=SchemaInfo)
async def analyze_schema(connection_id: str):
    """Analyze database schema."""
    connection = await store.get_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
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
    source_connection = await store.get_connection(source_connection_id)
    if not source_connection:
        raise HTTPException(status_code=404, detail="Source connection not found")
    
    target_connection = await store.get_connection(target_connection_id)
    if not target_connection:
        raise HTTPException(status_code=404, detail="Target connection not found")
    
    try:
        # Get source schema
        source_handler = get_database_handler(source_connection)
        source_handler.connect()
        source_schema = source_handler.extract_schema()
        source_handler.disconnect()
        
        # Get target schema
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
