"""
WebSocket route handlers
"""
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime
from core.auth import validate_jwt_token
from services.stats_collector import get_current_stats

logger = logging.getLogger(__name__)

async def handle_dashboard_websocket(websocket: WebSocket, manager):
    """Handle dashboard-specific WebSocket connections"""
    dashboard_user = "dashboard"
    await manager.connect(websocket, dashboard_user)
    
    try:
        # Send initial stats immediately upon connection
        stats = await get_current_stats()
        await websocket.send_text(json.dumps({
            "type": "stats_update",
            "data": stats
        }))
        
        await websocket.send_text(json.dumps({
            "type": "connection_status",
            "data": {
                "status": "connected",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        while True:
            # Wait for messages from dashboard client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif message["type"] == "request_stats":
                stats = await get_current_stats()
                await websocket.send_text(json.dumps({
                    "type": "stats_update",
                    "data": stats
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_user_websocket(websocket: WebSocket, user_id: str, manager):
    """Handle user-specific WebSocket connections"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "auth":
                # Extract and validate token
                token = None
                if "token" in message:
                    token = message["token"]
                elif "authenticated" in message and "token" in message["authenticated"]:
                    token = message["authenticated"]["token"]
                elif "authorization" in message:
                    token = message["authorization"].replace("Bearer ", "")
                
                if not token:
                    logger.warning(f"Auth message received but no token found")
                    await websocket.close(code=4001, reason="Missing token")
                    return
                
                validated_user = await validate_jwt_token(token.strip())
                if not validated_user:
                    logger.warning("Token validation failed")
                    await websocket.close(code=4001, reason="Invalid token")
                    return
                
                if str(message.get("user_id")) != str(validated_user):
                    logger.warning(f"User ID mismatch")
                    await websocket.close(code=4001, reason="User ID mismatch")
                    return
                
                # Send initial stats and welcome
                stats = await get_current_stats()
                await websocket.send_text(json.dumps({
                    "type": "stats_update",
                    "data": stats
                }))
                
                await websocket.send_text(json.dumps({
                    "type": "connection_status",
                    "data": {
                        "status": "authenticated",
                        "user_id": validated_user,
                        "timestamp": datetime.now().isoformat()
                    }
                }))
                
            elif message["type"] == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif message["type"] == "request_stats":
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