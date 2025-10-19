"""
Simple Persistent Connection Storage
A lightweight, efficient solution for storing database connections persistently.
"""
import sqlite3
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..models import DatabaseConnection

logger = logging.getLogger(__name__)

class ConnectionStore:
    """
    Simple, efficient persistent storage for database connections.
    Uses SQLite for reliability and simplicity.
    """
    
    def __init__(self, db_path: str = "connections.db"):
        """Initialize the connection store with SQLite database."""
        self.db_path = Path(db_path)
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create the database and table if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS connections (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        db_type TEXT NOT NULL,
                        host TEXT NOT NULL,
                        port INTEGER,
                        database_name TEXT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        ssl_mode TEXT DEFAULT 'disable',
                        ssl_cert TEXT,
                        ssl_key TEXT,
                        ssl_ca TEXT,
                        connection_params TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                conn.commit()
                logger.info("✅ Connection database initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    async def save_connection(self, connection: DatabaseConnection) -> str:
        """Save a connection to persistent storage."""
        try:
            # Generate ID if not present
            connection_id = connection.id or str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            # Serialize connection params
            params_json = json.dumps(connection.connection_params or {})
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO connections 
                    (id, name, db_type, host, port, database_name, username, password,
                     ssl_mode, ssl_cert, ssl_key, ssl_ca, connection_params, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    connection_id,
                    connection.name,
                    connection.db_type.value,
                    connection.host,
                    connection.port,
                    connection.database,
                    connection.username,
                    connection.password,
                    connection.ssl_mode.value if connection.ssl_mode else 'disable',
                    connection.ssl_cert,
                    connection.ssl_key,
                    connection.ssl_ca,
                    params_json,
                    now,
                    now
                ))
                conn.commit()
            
            logger.info(f"✅ Saved connection: {connection.name} ({connection_id})")
            return connection_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save connection: {e}")
            raise
    
    async def get_connection(self, connection_id: str) -> Optional[DatabaseConnection]:
        """Get a specific connection by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM connections WHERE id = ?", 
                    (connection_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # Parse connection params
                connection_params = json.loads(row['connection_params'] or '{}')
                
                # Create DatabaseConnection object
                return DatabaseConnection(
                    id=row['id'],
                    name=row['name'],
                    db_type=row['db_type'],
                    host=row['host'],
                    port=row['port'],
                    database=row['database_name'],
                    username=row['username'],
                    password=row['password'],
                    ssl_mode=row['ssl_mode'],
                    ssl_cert=row['ssl_cert'],
                    ssl_key=row['ssl_key'],
                    ssl_ca=row['ssl_ca'],
                    connection_params=connection_params
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to get connection {connection_id}: {e}")
            return None
    
    async def list_connections(self) -> List[Dict[str, Any]]:
        """List all connections with basic info."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT id, name, db_type, host, database_name, created_at 
                    FROM connections 
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                
                connections = []
                for row in rows:
                    connections.append({
                        "connection_id": row['id'],
                        "name": row['name'],
                        "database_type": row['db_type'],
                        "host": row['host'],
                        "database": row['database_name'],
                        "created_at": row['created_at']
                    })
                
                return connections
                
        except Exception as e:
            logger.error(f"❌ Failed to list connections: {e}")
            return []
    
    async def delete_connection(self, connection_id: str) -> bool:
        """Delete a connection."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM connections WHERE id = ?", 
                    (connection_id,)
                )
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"✅ Deleted connection: {connection_id}")
                else:
                    logger.warning(f"⚠️ Connection not found: {connection_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"❌ Failed to delete connection {connection_id}: {e}")
            return False
    
    async def connection_exists(self, connection_id: str) -> bool:
        """Check if a connection exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM connections WHERE id = ? LIMIT 1", 
                    (connection_id,)
                )
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"❌ Failed to check connection existence {connection_id}: {e}")
            return False

# Global store instance
_connection_store = None

def get_connection_store() -> ConnectionStore:
    """Get the global connection store instance."""
    global _connection_store
    if _connection_store is None:
        _connection_store = ConnectionStore()
    return _connection_store