"""
Webhook endpoints for push notifications
"""
from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime
from models.websocket_models import WebhookData
from services.stats_collector import get_current_stats

logger = logging.getLogger(__name__)

def create_webhook_router(manager):
    """Create webhook router with connection manager"""
    router = APIRouter(prefix="/webhooks", tags=["webhooks"])

    @router.post("/schema-generated")
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

    @router.post("/api-generated")
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

    @router.post("/project-created")
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

    @router.post("/user-joined")
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

    return router