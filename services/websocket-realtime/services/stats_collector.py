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

async def get_current_stats(user_id: str = None) -> Dict:
    """
    Get current statistics from all services with all required properties
    
    Args:
        user_id: Optional user ID to filter activities and stats for specific user
    """
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
        # Get activity tracking stats from project management service
        # This endpoint provides real-time dashboard stats
        try:
            activity_response = await client.get(f"{PROJECT_SERVICE_URL}/api/activity/stats")
            if activity_response.status_code == 200:
                activity_data = activity_response.json()
                # Check if we got the stats object or the wrapper
                if "stats" in activity_data:
                    activity_stats = activity_data["stats"]
                else:
                    activity_stats = activity_data
                # Map activity stats to dashboard stats
                stats["schemasGenerated"] = activity_stats.get("schema_generated", 0)
                stats["apisScaffolded"] = activity_stats.get("api_scaffolded", 0)
                stats["dataFilesCleaned"] = activity_stats.get("data_cleaned", 0)
                stats["activeDevelopers"] = activity_stats.get("unique_users", 0)
                stats["codeTemplatesGenerated"] = activity_stats.get("code_generated", 0)
                stats["migrationsCompleted"] = activity_stats.get("migration_completed", 0)
                logger.info(f"✅ Activity tracking stats retrieved: {activity_stats}")
            else:
                logger.warning(f"Activity stats endpoint returned status {activity_response.status_code}")
        except Exception as e:
            logger.error(f"❌ Failed to get activity tracking stats: {e}", exc_info=True)

        # Fetch recent activities for dashboard (filtered by user_id)
        try:
            # Build URL with user_id parameter if provided
            activities_url = f"{PROJECT_SERVICE_URL}/api/activity/recent?limit=5"
            if user_id:
                activities_url += f"&user_id={user_id}"
            
            recent_response = await client.get(activities_url)
            logger.info(f"🔍 Recent activities request for user {user_id}: status={recent_response.status_code}")
            if recent_response.status_code == 200:
                recent_data = recent_response.json()
                logger.info(f"🔍 Recent activities response type: {type(recent_data)}, keys: {recent_data.keys() if isinstance(recent_data, dict) else 'N/A'}")
                
                # Try to extract activities from possible wrappers
                activities = None
                if isinstance(recent_data, dict):
                    if "activities" in recent_data:
                        activities = recent_data["activities"]
                        logger.info(f"✅ Found activities in 'activities' key: {len(activities)} items")
                    elif "data" in recent_data and isinstance(recent_data["data"], list):
                        activities = recent_data["data"]
                        logger.info(f"✅ Found activities in 'data' key (list): {len(activities)} items")
                    elif isinstance(recent_data.get("data"), dict) and "activities" in recent_data["data"]:
                        activities = recent_data["data"]["activities"]
                        logger.info(f"✅ Found activities in 'data.activities': {len(activities)} items")
                if activities is None and isinstance(recent_data, list):
                    activities = recent_data
                    logger.info(f"✅ Found activities as direct list: {len(activities)} items")
                if activities is None:
                    activities = []
                    logger.warning("⚠️ Could not extract activities from response, using empty array")
                
                # Frontend expects "recentActivities" (plural with "recent")
                stats["recentActivities"] = activities
                stats["activityCount"] = len(activities)
                stats["hasRecentActivities"] = len(activities) > 0
                logger.info(f"✅ Recent activities attached to stats: count={len(activities)}, hasRecentActivities={len(activities) > 0}")
                logger.info(f"🔍 First activity preview: {activities[0] if activities else 'N/A'}")
            else:
                stats["recentActivities"] = []
                stats["activityCount"] = 0
                stats["hasRecentActivities"] = False
                logger.warning(f"⚠️ Recent activities endpoint returned status {recent_response.status_code}")
        except Exception as e:
            stats["recentActivities"] = []
            stats["activityCount"] = 0
            stats["hasRecentActivities"] = False
            logger.error(f"❌ Failed to get recent activities: {e}", exc_info=True)
        
        try:
            # Get schema detection stats
            schema_response = await client.get(f"{SCHEMA_SERVICE_URL}/stats")
            if schema_response.status_code == 200:
                schema_data = schema_response.json()
                stats["totalSchemas"] = schema_data.get("total_schemas", 0)
                # Use activity tracking count if available, otherwise fall back to schema service
                if stats["schemasGenerated"] == 0:
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
                # Use activity tracking count if available, otherwise fall back to code service
                if stats["apisScaffolded"] == 0:
                    stats["apisScaffolded"] = code_data.get("apis_scaffolded", code_data.get("total_apis", 0))
                if stats["codeTemplatesGenerated"] == 0:
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
                # Use activity tracking count if available, otherwise fall back to db service
                if stats["migrationsCompleted"] == 0:
                    stats["migrationsCompleted"] = db_data.get("migrations_completed", 0)
                if stats["dataFilesCleaned"] == 0:
                    stats["dataFilesCleaned"] = db_data.get("schemas_imported", 0)
                logger.debug(f"Database migration stats: {db_data}")
        except Exception as e:
            logger.warning(f"Failed to get database migration stats: {e}")
    
    # Ensure all numeric values are integers (but preserve recentActivities array and other special fields)
    for key, value in stats.items():
        if key not in ["lastUpdated", "systemHealth", "recentActivities", "hasRecentActivities"]:
            if value is None or value == "undefined":
                stats[key] = 0
            elif isinstance(value, str) and value.isdigit():
                stats[key] = int(value)
            elif not isinstance(value, int):
                stats[key] = 0
    
    logger.info(f"📊 Generated comprehensive stats with {stats.get('activityCount', 0)} activities")
    logger.info(f"🔍 recentActivities field present: {'recentActivities' in stats}, hasRecentActivities: {stats.get('hasRecentActivities', False)}")
    return stats