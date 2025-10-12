"""
Statistics collection from all microservices
"""
import httpx
import logging
from datetime import datetime
from typing import Dict
from config.settings import (
    SCHEMA_SERVICE_URL,
    PROJECT_SERVICE_URL, 
    CODE_SERVICE_URL,
    DATABASE_MIGRATION_SERVICE_URL
)

logger = logging.getLogger(__name__)

async def get_current_stats() -> Dict:
    """Get current statistics from all services with all required properties"""
    # Initialize with default values to prevent undefined errors
    stats = {
        # Core connection stats
        "totalConnections": 0,
        "activeUsers": 0,
        
        # Database and schema stats
        "totalSchemas": 0,
        "schemasGenerated": 0,
        "totalDatabaseConnections": 0,
        "activeDatabaseConnections": 0,
        
        # API and code generation stats
        "totalAPIs": 0,
        "apisScaffolded": 0,
        "codeTemplatesGenerated": 0,
        
        # Data processing stats
        "dataFilesCleaned": 0,
        "etlPipelinesRunning": 0,
        "migrationsCompleted": 0,
        
        # Project and collaboration stats
        "totalProjects": 0,
        "activeDevelopers": 0,
        "collaborativeSessions": 0,
        
        # System status
        "systemHealth": "healthy",
        "lastUpdated": datetime.now().isoformat()
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # Get schema detection stats
            schema_response = await client.get(f"{SCHEMA_SERVICE_URL}/stats")
            if schema_response.status_code == 200:
                schema_data = schema_response.json()
                stats["totalSchemas"] = schema_data.get("total_schemas", 0)
                stats["schemasGenerated"] = schema_data.get("schemas_generated", schema_data.get("total_schemas", 0))
                logger.debug(f"Schema stats: {schema_data}")
        except Exception as e:
            logger.warning(f"Failed to get schema stats: {e}")
        
        try:
            # Get project management stats
            project_response = await client.get(f"{PROJECT_SERVICE_URL}/stats")
            if project_response.status_code == 200:
                project_data = project_response.json()
                stats["totalProjects"] = project_data.get("total_projects", 0)
                stats["collaborativeSessions"] = project_data.get("active_collaborations", 0)
                logger.debug(f"Project stats: {project_data}")
        except Exception as e:
            logger.warning(f"Failed to get project stats: {e}")
        
        try:
            # Get code generation stats
            code_response = await client.get(f"{CODE_SERVICE_URL}/stats")
            if code_response.status_code == 200:
                code_data = code_response.json()
                stats["totalAPIs"] = code_data.get("total_apis", 0)
                stats["apisScaffolded"] = code_data.get("apis_scaffolded", code_data.get("total_apis", 0))
                stats["codeTemplatesGenerated"] = code_data.get("templates_generated", 0)
                logger.debug(f"Code generation stats: {code_data}")
        except Exception as e:
            logger.warning(f"Failed to get code generation stats: {e}")
        
        try:
            # Get database migration stats
            db_response = await client.get(f"{DATABASE_MIGRATION_SERVICE_URL}/api/database/stats")
            if db_response.status_code == 200:
                db_data = db_response.json()
                stats["totalDatabaseConnections"] = db_data.get("total_connections", 0)
                stats["activeDatabaseConnections"] = db_data.get("active_connections", 0)
                stats["migrationsCompleted"] = db_data.get("migrations_completed", 0)
                stats["dataFilesCleaned"] = db_data.get("schemas_imported", 0)
                logger.debug(f"Database migration stats: {db_data}")
        except Exception as e:
            logger.warning(f"Failed to get database migration stats: {e}")
    
    # Ensure all numeric values are integers
    for key, value in stats.items():
        if key not in ["lastUpdated", "systemHealth"]:
            if value is None or value == "undefined":
                stats[key] = 0
            elif isinstance(value, str) and value.isdigit():
                stats[key] = int(value)
            elif not isinstance(value, int):
                stats[key] = 0
    
    logger.info(f"Generated comprehensive stats: {stats}")
    return stats