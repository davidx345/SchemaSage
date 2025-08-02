"""
Integration Management API Routes

Routes for managing various integrations including webhooks,
notifications, cloud storage, BI tools, data catalogs, and custom APIs.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from integrations.manager import IntegrationManager

# Create integration manager instance
integration_manager = IntegrationManager()

# Register integrations with default configs
from integrations.webhook import WebhookIntegration
from integrations.notification import NotificationIntegration
from integrations.cloud_storage import CloudStorageIntegration
from integrations.bi_tools import BIToolsIntegration
from integrations.data_catalogs import DataCatalogsIntegration
from integrations.custom_api import CustomAPIIntegration

# Default configurations
default_webhook_config = {"enabled": False, "webhooks": [], "events": []}
integration_manager.register("webhook", WebhookIntegration, default_webhook_config)

notification_default_config = {"enabled": False, "channels": [], "events": []}
integration_manager.register("notification", NotificationIntegration, notification_default_config)

cloud_storage_default_config = {"enabled": False, "providers": []}
integration_manager.register("cloud_storage", CloudStorageIntegration, cloud_storage_default_config)

bi_tools_default_config = {"enabled": False, "tools": []}
integration_manager.register("bi_tools", BIToolsIntegration, bi_tools_default_config)

data_catalogs_default_config = {"enabled": False, "catalogs": []}
integration_manager.register("data_catalogs", DataCatalogsIntegration, data_catalogs_default_config)

custom_api_default_config = {"enabled": False, "connectors": []}
integration_manager.register("custom_api", CustomAPIIntegration, custom_api_default_config)

# Router for integration endpoints
router = APIRouter(prefix="/integrations", tags=["integrations"])


# Request/Response Models
class WebhookConfigRequest(BaseModel):
    webhooks: List[Dict[str, Any]]
    events: List[str]
    enabled: bool = True


class WebhookTriggerRequest(BaseModel):
    event: str
    payload: Dict[str, Any]


class NotificationConfigRequest(BaseModel):
    channels: List[Dict[str, Any]]
    events: List[str]
    enabled: bool = True


class NotificationTriggerRequest(BaseModel):
    event: str
    payload: Dict[str, Any]


class CloudStorageConfigRequest(BaseModel):
    providers: List[Dict[str, Any]]
    enabled: bool = True


class CloudStorageTriggerRequest(BaseModel):
    event: str
    payload: Dict[str, Any]


class BIToolsConfigRequest(BaseModel):
    tools: List[Dict[str, Any]]
    enabled: bool = True


class BIToolsTriggerRequest(BaseModel):
    event: str
    payload: Dict[str, Any]


class DataCatalogsConfigRequest(BaseModel):
    catalogs: List[Dict[str, Any]]
    enabled: bool = True


class DataCatalogsTriggerRequest(BaseModel):
    event: str
    payload: Dict[str, Any]


class CustomAPIConfigRequest(BaseModel):
    connectors: List[Dict[str, Any]]
    enabled: bool = True


class CustomAPITriggerRequest(BaseModel):
    event: str
    payload: Dict[str, Any]


# Webhook Integration Endpoints
@router.get("/webhooks")
async def get_webhook_config():
    """Get current webhook integration config"""
    webhook = integration_manager.integrations.get("webhook")
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook integration not found")
    return {
        "enabled": webhook.enabled,
        "webhooks": webhook.webhooks,
        "events": webhook.events
    }


@router.post("/webhooks")
async def configure_webhook(config: WebhookConfigRequest):
    """Configure webhook integration"""
    webhook = integration_manager.integrations.get("webhook")
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook integration not found")
    integration_manager.configure("webhook", config.dict())
    return {"success": True}


@router.post("/webhooks/enable")
async def enable_webhook():
    integration_manager.enable("webhook")
    return {"success": True}


@router.post("/webhooks/disable")
async def disable_webhook():
    integration_manager.disable("webhook")
    return {"success": True}


@router.post("/webhooks/trigger")
async def trigger_webhook(req: WebhookTriggerRequest):
    webhook = integration_manager.integrations.get("webhook")
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook integration not found")
    integration_manager.trigger("webhook", req.event, req.payload)
    return {"success": True}


# Notification Integration Endpoints
@router.get("/notifications")
async def get_notification_config():
    """Get current notification integration config"""
    notification = integration_manager.integrations.get("notification")
    if not notification:
        raise HTTPException(status_code=404, detail="Notification integration not found")
    return {
        "enabled": notification.enabled,
        "channels": notification.channels,
        "events": notification.events
    }


@router.post("/notifications")
async def configure_notification(config: NotificationConfigRequest):
    """Configure notification integration"""
    notification = integration_manager.integrations.get("notification")
    if not notification:
        raise HTTPException(status_code=404, detail="Notification integration not found")
    integration_manager.configure("notification", config.dict())
    return {"success": True}


@router.post("/notifications/enable")
async def enable_notification():
    integration_manager.enable("notification")
    return {"success": True}


@router.post("/notifications/disable")
async def disable_notification():
    integration_manager.disable("notification")
    return {"success": True}


@router.post("/notifications/trigger")
async def trigger_notification(req: NotificationTriggerRequest):
    notification = integration_manager.integrations.get("notification")
    if not notification:
        raise HTTPException(status_code=404, detail="Notification integration not found")
    integration_manager.trigger("notification", req.event, req.payload)
    return {"success": True}


# Cloud Storage Integration Endpoints
@router.get("/cloud-storage")
async def get_cloud_storage_config():
    """Get current cloud storage integration config"""
    cloud_storage = integration_manager.integrations.get("cloud_storage")
    if not cloud_storage:
        raise HTTPException(status_code=404, detail="Cloud storage integration not found")
    return {
        "enabled": cloud_storage.enabled,
        "providers": cloud_storage.providers
    }


@router.post("/cloud-storage")
async def configure_cloud_storage(config: CloudStorageConfigRequest):
    """Configure cloud storage integration"""
    cloud_storage = integration_manager.integrations.get("cloud_storage")
    if not cloud_storage:
        raise HTTPException(status_code=404, detail="Cloud storage integration not found")
    integration_manager.configure("cloud_storage", config.dict())
    return {"success": True}


@router.post("/cloud-storage/enable")
async def enable_cloud_storage():
    integration_manager.enable("cloud_storage")
    return {"success": True}


@router.post("/cloud-storage/disable")
async def disable_cloud_storage():
    integration_manager.disable("cloud_storage")
    return {"success": True}


@router.post("/cloud-storage/trigger")
async def trigger_cloud_storage(req: CloudStorageTriggerRequest):
    cloud_storage = integration_manager.integrations.get("cloud_storage")
    if not cloud_storage:
        raise HTTPException(status_code=404, detail="Cloud storage integration not found")
    integration_manager.trigger("cloud_storage", req.event, req.payload)
    return {"success": True}


# BI Tools Integration Endpoints
@router.get("/bi-tools")
async def get_bi_tools_config():
    """Get current BI tools integration config"""
    bi_tools = integration_manager.integrations.get("bi_tools")
    if not bi_tools:
        raise HTTPException(status_code=404, detail="BI tools integration not found")
    return {
        "enabled": bi_tools.enabled,
        "tools": bi_tools.tools
    }


@router.post("/bi-tools")
async def configure_bi_tools(config: BIToolsConfigRequest):
    """Configure BI tools integration"""
    bi_tools = integration_manager.integrations.get("bi_tools")
    if not bi_tools:
        raise HTTPException(status_code=404, detail="BI tools integration not found")
    integration_manager.configure("bi_tools", config.dict())
    return {"success": True}


@router.post("/bi-tools/enable")
async def enable_bi_tools():
    integration_manager.enable("bi_tools")
    return {"success": True}


@router.post("/bi-tools/disable")
async def disable_bi_tools():
    integration_manager.disable("bi_tools")
    return {"success": True}


@router.post("/bi-tools/trigger")
async def trigger_bi_tools(req: BIToolsTriggerRequest):
    bi_tools = integration_manager.integrations.get("bi_tools")
    if not bi_tools:
        raise HTTPException(status_code=404, detail="BI tools integration not found")
    integration_manager.trigger("bi_tools", req.event, req.payload)
    return {"success": True}


# Data Catalogs Integration Endpoints
@router.get("/data-catalogs")
async def get_data_catalogs_config():
    """Get current data catalogs integration config"""
    data_catalogs = integration_manager.integrations.get("data_catalogs")
    if not data_catalogs:
        raise HTTPException(status_code=404, detail="Data catalogs integration not found")
    return {
        "enabled": data_catalogs.enabled,
        "catalogs": data_catalogs.catalogs
    }


@router.post("/data-catalogs")
async def configure_data_catalogs(config: DataCatalogsConfigRequest):
    """Configure data catalogs integration"""
    data_catalogs = integration_manager.integrations.get("data_catalogs")
    if not data_catalogs:
        raise HTTPException(status_code=404, detail="Data catalogs integration not found")
    integration_manager.configure("data_catalogs", config.dict())
    return {"success": True}


@router.post("/data-catalogs/enable")
async def enable_data_catalogs():
    integration_manager.enable("data_catalogs")
    return {"success": True}


@router.post("/data-catalogs/disable")
async def disable_data_catalogs():
    integration_manager.disable("data_catalogs")
    return {"success": True}


@router.post("/data-catalogs/trigger")
async def trigger_data_catalogs(req: DataCatalogsTriggerRequest):
    data_catalogs = integration_manager.integrations.get("data_catalogs")
    if not data_catalogs:
        raise HTTPException(status_code=404, detail="Data catalogs integration not found")
    integration_manager.trigger("data_catalogs", req.event, req.payload)
    return {"success": True}


# Custom API Integration Endpoints
@router.get("/custom-api")
async def get_custom_api_config():
    """Get current custom API integration config"""
    custom_api = integration_manager.integrations.get("custom_api")
    if not custom_api:
        raise HTTPException(status_code=404, detail="Custom API integration not found")
    return {
        "enabled": custom_api.enabled,
        "connectors": custom_api.connectors
    }


@router.post("/custom-api")
async def configure_custom_api(config: CustomAPIConfigRequest):
    """Configure custom API integration"""
    custom_api = integration_manager.integrations.get("custom_api")
    if not custom_api:
        raise HTTPException(status_code=404, detail="Custom API integration not found")
    integration_manager.configure("custom_api", config.dict())
    return {"success": True}


@router.post("/custom-api/enable")
async def enable_custom_api():
    integration_manager.enable("custom_api")
    return {"success": True}


@router.post("/custom-api/disable")
async def disable_custom_api():
    integration_manager.disable("custom_api")
    return {"success": True}


@router.post("/custom-api/trigger")
async def trigger_custom_api(req: CustomAPITriggerRequest):
    custom_api = integration_manager.integrations.get("custom_api")
    if not custom_api:
        raise HTTPException(status_code=404, detail="Custom API integration not found")
    integration_manager.trigger("custom_api", req.event, req.payload)
    return {"success": True}
