"""
WebSocket Real-time Service
Handles real-time dashboard updates and push notifications
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
from jose import jwt
import asyncio
import httpx
import logging
import os
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_jwt_secret_key_not_for_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Service URLs
SCHEMA_SERVICE_URL = os.getenv("SCHEMA_DETECTION_SERVICE_URL", "https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com")
PROJECT_SERVICE_URL = os.getenv("PROJECT_MANAGEMENT_SERVICE_URL", "https://schemasage-project-management-48496f02644b.herokuapp.com")
CODE_SERVICE_URL = os.getenv("CODE_GENERATION_SERVICE_URL", "https://schemasage-code-generation-56faa300323b.herokuapp.com")
AUTH_SERVICE_URL = os.getenv("AUTHENTICATION_SERVICE_URL", "https://schemasage-auth-9d6de1a32af9.herokuapp.com")

# CORS Origins - Allow your frontend
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://schemasage.vercel.app,http://localhost:3000").split(",")

# Data models
class WebhookData(BaseModel):
    user: str
    timestamp: str
    project: Optional[str] = None
    project_name: Optional[str] = None
    schema_type: Optional[str] = None
    framework: Optional[str] = None
    tables_count: Optional[int] = None
    project_type: Optional[str] = None

class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_sessions: Dict[WebSocket, str] = {}
        self.connection_count = 0
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.user_sessions[websocket] = user_id
        self.connection_count += 1
        
        logger.info(f"User {user_id} connected. Total connections: {self.connection_count}")
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.user_sessions:
            user_id = self.user_sessions[websocket]
            
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # Remove user entry if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            del self.user_sessions[websocket]
            self.connection_count -= 1
            
            logger.info(f"User {user_id} disconnected. Total connections: {self.connection_count}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to user {user_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users"""
        message_str = json.dumps(message)
        disconnected = []
        
        for user_id, connections in self.active_connections.items():
            for websocket in connections.copy():
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.warning(f"Failed to broadcast to user {user_id}: {e}")
                    disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_active_user_count(self) -> int:
        """Get number of unique active users"""
        return len(self.active_connections)
    
    def get_total_connection_count(self) -> int:
        """Get total number of active connections"""
        return self.connection_count

# Global connection manager
manager = ConnectionManager()

async def validate_jwt_token(token: str) -> Optional[str]:
    """Validate JWT token and return user ID"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        return user_id
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None

async def get_current_stats() -> dict:
    """Get current statistics from all services"""
    stats = {
        "totalSchemas": 0,
        "totalAPIs": 0,
        "totalProjects": 0,
        "activeUsers": manager.get_active_user_count(),
        "totalConnections": manager.get_total_connection_count(),
        "lastUpdated": datetime.now().isoformat()
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # Get schema stats
            schema_response = await client.get(f"{SCHEMA_SERVICE_URL}/stats")
            if schema_response.status_code == 200:
                schema_data = schema_response.json()
                stats["totalSchemas"] = schema_data.get("total_schemas", 0)
        except Exception as e:
            logger.warning(f"Failed to get schema stats: {e}")
        
        try:
            # Get project stats
            project_response = await client.get(f"{PROJECT_SERVICE_URL}/stats")
            if project_response.status_code == 200:
                project_data = project_response.json()
                stats["totalProjects"] = project_data.get("total_projects", 0)
        except Exception as e:
            logger.warning(f"Failed to get project stats: {e}")
        
        try:
            # Get code generation stats (if endpoint exists)
            code_response = await client.get(f"{CODE_SERVICE_URL}/stats")
            if code_response.status_code == 200:
                code_data = code_response.json()
                stats["totalAPIs"] = code_data.get("total_apis", 0)
        except Exception as e:
            logger.warning(f"Failed to get code generation stats: {e}")
    
    return stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("WebSocket Real-time Service starting up...")
    
    # Start background task for periodic stats updates
    asyncio.create_task(periodic_stats_broadcast())
    
    yield
    
    logger.info("WebSocket Real-time Service shutting down...")

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

async def periodic_stats_broadcast():
    """Periodically broadcast stats updates"""
    while True:
        try:
            await asyncio.sleep(60)  # Update every minute
            
            if manager.get_total_connection_count() > 0:
                stats = await get_current_stats()
                await manager.broadcast_to_all({
                    "type": "stats_update",
                    "data": stats
                })
                logger.info(f"Broadcasted stats update to {manager.get_total_connection_count()} connections")
        
        except Exception as e:
            logger.error(f"Error in periodic stats broadcast: {e}")

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Main WebSocket endpoint for real-time connections"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "auth":
                # Validate JWT token
                token = message.get("token")
                if not token:
                    await websocket.close(code=4001, reason="Missing token")
                    return
                
                validated_user = await validate_jwt_token(token)
                if not validated_user:
                    await websocket.close(code=4001, reason="Invalid token")
                    return
                
                # Send initial stats after successful authentication
                stats = await get_current_stats()
                await websocket.send_text(json.dumps({
                    "type": "stats_update",
                    "data": stats
                }))
                
                # Send welcome message
                await websocket.send_text(json.dumps({
                    "type": "connection_status",
                    "data": {
                        "status": "authenticated",
                        "user_id": validated_user,
                        "timestamp": datetime.now().isoformat()
                    }
                }))
                
            elif message["type"] == "ping":
                # Respond to ping with pong
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif message["type"] == "request_stats":
                # Send current stats on demand
                stats = await get_current_stats()
                await websocket.send_text(json.dumps({
                    "type": "stats_update",
                    "data": stats
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket)

# Webhook endpoints for push notifications

@app.post("/webhooks/schema-generated")
async def schema_generated_webhook(data: WebhookData):
    """Receive notification when schema is generated"""
    try:
        # Broadcast activity update
        await manager.broadcast_to_all({
            "type": "activity_update",
            "data": {
                "id": f"schema_{datetime.now().timestamp()}",
                "activity": "Schema Generated",
                "user": data.user,
                "project": data.project or "Unknown",
                "details": f"Schema type: {data.schema_type or 'Unknown'}",
                "timestamp": data.timestamp,
                "icon": "database"
            }
        })
        
        # Update and broadcast current stats
        stats = await get_current_stats()
        await manager.broadcast_to_all({
            "type": "stats_update",
            "data": stats
        })
        
        logger.info(f"Schema generated webhook processed for user {data.user}")
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing schema generated webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@app.post("/webhooks/api-generated")
async def api_generated_webhook(data: WebhookData):
    """Receive notification when API is generated"""
    try:
        # Broadcast activity update
        await manager.broadcast_to_all({
            "type": "activity_update",
            "data": {
                "id": f"api_{datetime.now().timestamp()}",
                "activity": "API Generated",
                "user": data.user,
                "project": data.project or "Unknown",
                "details": f"Framework: {data.framework or 'Unknown'}, Tables: {data.tables_count or 0}",
                "timestamp": data.timestamp,
                "icon": "code"
            }
        })
        
        # Update and broadcast current stats
        stats = await get_current_stats()
        await manager.broadcast_to_all({
            "type": "stats_update",
            "data": stats
        })
        
        logger.info(f"API generated webhook processed for user {data.user}")
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing API generated webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@app.post("/webhooks/project-created")
async def project_created_webhook(data: WebhookData):
    """Receive notification when project is created"""
    try:
        # Broadcast activity update
        await manager.broadcast_to_all({
            "type": "activity_update",
            "data": {
                "id": f"project_{datetime.now().timestamp()}",
                "activity": "Project Created",
                "user": data.user,
                "project": data.project_name or "Unknown",
                "details": f"Type: {data.project_type or 'Standard'}",
                "timestamp": data.timestamp,
                "icon": "folder"
            }
        })
        
        # Update and broadcast current stats
        stats = await get_current_stats()
        await manager.broadcast_to_all({
            "type": "stats_update",
            "data": stats
        })
        
        logger.info(f"Project created webhook processed for user {data.user}")
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing project created webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@app.post("/webhooks/user-joined")
async def user_joined_webhook(data: WebhookData):
    """Receive notification when user joins"""
    try:
        # Broadcast activity update
        await manager.broadcast_to_all({
            "type": "activity_update",
            "data": {
                "id": f"user_{datetime.now().timestamp()}",
                "activity": "User Joined",
                "user": data.user,
                "project": "SchemaSage",
                "details": "New user registered",
                "timestamp": data.timestamp,
                "icon": "user-plus"
            }
        })
        
        # Update and broadcast current stats
        stats = await get_current_stats()
        await manager.broadcast_to_all({
            "type": "stats_update",
            "data": stats
        })
        
        logger.info(f"User joined webhook processed for user {data.user}")
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing user joined webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

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
    return await get_current_stats()

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
