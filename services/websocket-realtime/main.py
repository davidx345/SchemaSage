"""
WebSocket Real-time Service - Clean, Modular Architecture
Handles real-time dashboard updates and push notifications
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager

# Local imports
from config.settings import CORS_ORIGINS, STATS_UPDATE_INTERVAL
from core.connection_manager import ConnectionManager
from services.stats_collector import get_current_stats
from routes.websocket_routes import handle_dashboard_websocket, handle_user_websocket
from routes.dashboard_api import create_dashboard_router
from routes.webhook_routes import create_webhook_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global connection manager
manager = ConnectionManager()

async def periodic_stats_broadcast():
    """Periodically broadcast stats updates"""
    while True:
        try:
            await asyncio.sleep(STATS_UPDATE_INTERVAL)
            
            if manager.get_total_connection_count() > 0:
                stats = await get_current_stats()
                # Update stats with current connection info
                stats["totalConnections"] = manager.get_total_connection_count()
                stats["activeUsers"] = manager.get_active_user_count()
                stats["activeDevelopers"] = manager.get_active_user_count()
                
                await manager.broadcast_to_all({
                    "type": "stats_update",
                    "data": stats
                })
                logger.info(f"Broadcasted stats update to {manager.get_total_connection_count()} connections")
        
        except Exception as e:
            logger.error(f"Error in periodic stats broadcast: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("WebSocket Real-time Service starting up...")
    
    # Start background task for periodic stats updates
    asyncio.create_task(periodic_stats_broadcast())
    
    yield
    
    logger.info("WebSocket Real-time Service shutting down...")

# Create FastAPI app
app = FastAPI(
    title="WebSocket Real-time Service",
    description="Real-time dashboard updates and push notifications",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket endpoints
@app.websocket("/ws/dashboard")
async def dashboard_websocket_endpoint(websocket: WebSocket):
    """Dashboard-specific WebSocket endpoint"""
    await handle_dashboard_websocket(websocket, manager)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Main WebSocket endpoint for real-time connections"""
    await handle_user_websocket(websocket, user_id, manager)

# Include API routers
app.include_router(create_dashboard_router(manager))
app.include_router(create_webhook_router(manager))

# Health and info endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "websocket-realtime",
        "version": "1.0.0",
        "active_connections": manager.get_total_connection_count(),
        "active_users": manager.get_active_user_count(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "WebSocket Real-time Service",
        "version": "1.0.0",
        "status": "running",
        "active_connections": manager.get_total_connection_count(),
        "active_users": manager.get_active_user_count(),
        "features": [
            "Real-time dashboard updates",
            "Push notifications",
            "User activity tracking",
            "Statistics broadcasting",
            "WebSocket connection management"
        ],
        "endpoints": {
            "websocket": "WS /ws/{user_id}",
            "dashboard_websocket": "WS /ws/dashboard",
            "dashboard_broadcast": "POST /api/dashboard/broadcast",
            "dashboard_activity": "POST /api/dashboard/activity", 
            "dashboard_increment": "POST /api/dashboard/increment-stat",
            "dashboard_stats": "GET /api/dashboard/stats",
            "schema_webhook": "POST /webhooks/schema-generated",
            "api_webhook": "POST /webhooks/api-generated", 
            "project_webhook": "POST /webhooks/project-created",
            "user_webhook": "POST /webhooks/user-joined",
            "health": "GET /health"
        }
    }

@app.get("/stats")
async def get_stats():
    """Get current service statistics"""
    stats = await get_current_stats()
    # Include WebSocket connection stats
    stats["totalConnections"] = manager.get_total_connection_count()
    stats["activeUsers"] = manager.get_active_user_count()
    stats["activeDevelopers"] = manager.get_active_user_count()
    return stats

@app.get("/connections")
async def get_connections():
    """Get connection information (for debugging)"""
    return {
        "total_connections": manager.get_total_connection_count(),
        "active_users": manager.get_active_user_count(),
        "user_list": list(manager.active_connections.keys()),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
