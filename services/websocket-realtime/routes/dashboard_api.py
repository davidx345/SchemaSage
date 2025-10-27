"""
Dashboard API endpoints for microservice integration
"""
from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime
from models.websocket_models import DashboardUpdate, ActivityUpdate, StatIncrement
from services.stats_collector import get_current_stats

logger = logging.getLogger(__name__)

def create_dashboard_router(manager):
    """Create dashboard API router with connection manager"""
    router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

    @router.post("/broadcast")
    async def broadcast_dashboard_update(update: DashboardUpdate):
        """Broadcast real-time updates to all dashboard clients"""
        try:
            await manager.broadcast_to_all(update.dict())
            logger.info(f"Broadcasted dashboard update: {update.type}")
            return {"status": "success", "message": "Update broadcasted"}
        except Exception as e:
            logger.error(f"Failed to broadcast dashboard update: {e}")
            raise HTTPException(status_code=500, detail="Broadcast failed")

    @router.post("/activity")
    async def broadcast_activity_update(activity: ActivityUpdate):
        """Broadcast activity update to dashboard clients"""
        try:
            await manager.broadcast_to_all({
                "type": "activity_update",
                "data": activity.dict()
            })
            
            # Also trigger stats update
            stats = await get_current_stats()
            await manager.broadcast_to_all({
                "type": "stats_update",
                "data": stats
            })
            
            logger.info(f"Broadcasted activity update: {activity.type} - {activity.description}")
            return {"status": "success", "message": "Activity broadcasted"}
        except Exception as e:
            logger.error(f"Failed to broadcast activity: {e}")
            raise HTTPException(status_code=500, detail="Activity broadcast failed")

    @router.post("/increment-stat")
    async def increment_dashboard_stat(stat: StatIncrement):
        """Increment dashboard statistics"""
        try:
            # Trigger a stats refresh since we're fetching live stats from services
            stats = await get_current_stats()
            await manager.broadcast_to_all({
                "type": "stats_update",
                "data": stats
            })
            
            logger.info(f"Incremented stat {stat.metric} by {stat.value}")
            return {"status": "success", "message": f"Stat {stat.metric} incremented"}
        except Exception as e:
            logger.error(f"Failed to increment stat: {e}")
            raise HTTPException(status_code=500, detail="Stat increment failed")

    @router.post("/broadcast-stats")
    async def broadcast_stats_now(request: dict = None):
        """
        ⚡ INSTANT STATS BROADCAST
        
        Triggers an immediate broadcast of current dashboard stats to all 
        connected WebSocket clients. Called when a user becomes active or 
        performs an important action.
        
        This bypasses the periodic timer to provide instant real-time updates
        for activeDevelopers and other metrics.
        """
        try:
            # Fetch the latest stats from all services
            stats = await get_current_stats()
            
            # Update connection-based stats
            stats["totalConnections"] = manager.get_total_connection_count()
            stats["activeUsers"] = manager.get_active_user_count()
            
            # Broadcast to all connected clients
            await manager.broadcast_to_all({
                "type": "stats_update",
                "data": stats
            })
            
            logger.info(f"⚡ Instant stats broadcast to {manager.get_total_connection_count()} clients")
            return {
                "status": "success", 
                "message": "Stats broadcasted instantly",
                "clients_notified": manager.get_total_connection_count()
            }
        except Exception as e:
            logger.error(f"Failed to broadcast stats instantly: {e}")
            raise HTTPException(status_code=500, detail="Instant broadcast failed")

    @router.get("/stats")
    async def get_dashboard_stats():
        """Get current dashboard statistics"""
        try:
            stats = await get_current_stats()
            return {"status": "success", "data": stats}
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve stats")

    return router