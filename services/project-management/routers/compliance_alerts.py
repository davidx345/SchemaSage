"""
Compliance Alert System Router
Handles webhook configuration and real-time compliance notifications
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
import json
import uuid
import os
import httpx
import asyncio
from core.auth import get_current_user

router = APIRouter(prefix="/compliance-alerts", tags=["compliance-alerts"])

# Environment variables
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")

# Models
class WebhookConfiguration(BaseModel):
    type: str = Field(..., description="Webhook type: slack, teams, custom")
    webhook_url: HttpUrl
    channel: Optional[str] = None
    events: List[str] = Field(..., description="Events to listen for")
    severity_filter: Optional[List[str]] = ["critical", "high"]
    custom_message_template: Optional[str] = None
    active: bool = True

class ComplianceAlert(BaseModel):
    violation_type: str
    severity: str = Field(..., description="critical, high, medium, low")
    table_name: str
    column_name: Optional[str] = None
    description: str
    recommendation: str
    project_id: str

class NotificationHistory(BaseModel):
    id: str
    type: str
    severity: str
    message: str
    destination: str
    status: str
    sent_at: datetime
    project_id: Optional[str] = None

# Mock storage for webhooks and notifications
WEBHOOK_CONFIGURATIONS = {}
NOTIFICATION_HISTORY = []

async def send_slack_notification(webhook_url: str, message: Dict[str, Any]) -> bool:
    """Send notification to Slack"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json={
                    "text": message.get("text", "Compliance Alert"),
                    "attachments": [
                        {
                            "color": "danger" if message.get("severity") == "critical" else "warning",
                            "fields": [
                                {"title": "Severity", "value": message.get("severity", "unknown"), "short": True},
                                {"title": "Table", "value": message.get("table_name", "unknown"), "short": True},
                                {"title": "Description", "value": message.get("description", ""), "short": False},
                                {"title": "Recommendation", "value": message.get("recommendation", ""), "short": False}
                            ],
                            "footer": "SchemaSage Compliance Monitor",
                            "ts": int(datetime.now().timestamp())
                        }
                    ]
                }
            )
            return response.status_code == 200
    except Exception:
        return False

async def send_teams_notification(webhook_url: str, message: Dict[str, Any]) -> bool:
    """Send notification to Microsoft Teams"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json={
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "d63333" if message.get("severity") == "critical" else "ff8c00",
                    "summary": f"Compliance Alert: {message.get('violation_type', 'Unknown')}",
                    "sections": [
                        {
                            "activityTitle": "🚨 Compliance Alert",
                            "activitySubtitle": f"Severity: {message.get('severity', 'unknown').upper()}",
                            "facts": [
                                {"name": "Table", "value": message.get("table_name", "unknown")},
                                {"name": "Column", "value": message.get("column_name", "N/A")},
                                {"name": "Description", "value": message.get("description", "")},
                                {"name": "Recommendation", "value": message.get("recommendation", "")}
                            ],
                            "markdown": True
                        }
                    ]
                }
            )
            return response.status_code == 200
    except Exception:
        return False

async def send_custom_webhook(webhook_url: str, message: Dict[str, Any]) -> bool:
    """Send notification to custom webhook"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json={
                "event": "compliance_alert",
                "data": message,
                "timestamp": datetime.now().isoformat()
            })
            return response.status_code == 200
    except Exception:
        return False

async def process_notification(webhook_config: Dict[str, Any], alert_data: Dict[str, Any]):
    """Process and send notification based on webhook configuration"""
    notification_id = f"notif_{uuid.uuid4().hex[:16]}"
    
    # Check if severity matches filter
    if webhook_config.get("severity_filter") and alert_data.get("severity") not in webhook_config["severity_filter"]:
        return
    
    # Prepare message
    message = alert_data.copy()
    if webhook_config.get("custom_message_template"):
        template = webhook_config["custom_message_template"]
        message["text"] = template.format(**alert_data)
    else:
        message["text"] = f"🚨 Compliance Alert: {alert_data.get('violation_type', 'Unknown')} in {alert_data.get('table_name', 'unknown table')}"
    
    # Send notification based on type
    success = False
    webhook_type = webhook_config["type"]
    webhook_url = str(webhook_config["webhook_url"])
    
    if webhook_type == "slack":
        success = await send_slack_notification(webhook_url, message)
    elif webhook_type == "teams":
        success = await send_teams_notification(webhook_url, message)
    elif webhook_type == "custom":
        success = await send_custom_webhook(webhook_url, message)
    
    # Record notification history
    notification_record = {
        "id": notification_id,
        "type": webhook_type,
        "severity": alert_data.get("severity", "unknown"),
        "message": message.get("text", ""),
        "destination": webhook_config.get("channel", webhook_url),
        "status": "sent" if success else "failed",
        "sent_at": datetime.now().isoformat(),
        "project_id": alert_data.get("project_id")
    }
    
    NOTIFICATION_HISTORY.append(notification_record)

@router.post("/webhooks")
async def configure_webhook(
    webhook_config: WebhookConfiguration,
    current_user: dict = Depends(get_current_user)
):
    """Configure Slack/Teams webhooks"""
    try:
        user_id = current_user["sub"]
        webhook_id = f"webhook_{uuid.uuid4().hex[:16]}"
        
        # Validate webhook URL by sending test message
        test_message = {
            "text": "🔧 SchemaSage webhook configured successfully",
            "severity": "info",
            "table_name": "test",
            "description": "This is a test notification to verify webhook configuration",
            "recommendation": "No action required - this is a test"
        }
        
        # Test the webhook
        webhook_type = webhook_config.type
        webhook_url = str(webhook_config.webhook_url)
        test_success = False
        
        if webhook_type == "slack":
            test_success = await send_slack_notification(webhook_url, test_message)
        elif webhook_type == "teams":
            test_success = await send_teams_notification(webhook_url, test_message)
        elif webhook_type == "custom":
            test_success = await send_custom_webhook(webhook_url, test_message)
        
        if not test_success:
            raise HTTPException(status_code=400, detail="Failed to send test notification to webhook URL")
        
        # Store webhook configuration
        webhook_data = webhook_config.dict()
        webhook_data["id"] = webhook_id
        webhook_data["user_id"] = user_id
        webhook_data["created_at"] = datetime.now().isoformat()
        
        if user_id not in WEBHOOK_CONFIGURATIONS:
            WEBHOOK_CONFIGURATIONS[user_id] = []
        
        WEBHOOK_CONFIGURATIONS[user_id].append(webhook_data)
        
        return {
            "success": True,
            "data": {
                "webhook_id": webhook_id,
                "status": "configured",
                "test_sent": True
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure webhook: {str(e)}")

@router.get("/webhooks")
async def list_webhooks(current_user: dict = Depends(get_current_user)):
    """List configured webhooks"""
    try:
        user_id = current_user["sub"]
        user_webhooks = WEBHOOK_CONFIGURATIONS.get(user_id, [])
        
        return {
            "success": True,
            "data": {
                "webhooks": user_webhooks,
                "total_count": len(user_webhooks)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")

@router.delete("/webhooks/{webhook_id}")
async def remove_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove webhook configuration"""
    try:
        user_id = current_user["sub"]
        user_webhooks = WEBHOOK_CONFIGURATIONS.get(user_id, [])
        
        # Find and remove webhook
        webhook_index = next((i for i, w in enumerate(user_webhooks) if w["id"] == webhook_id), None)
        if webhook_index is None:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        removed_webhook = user_webhooks.pop(webhook_index)
        
        return {
            "success": True,
            "data": {
                "webhook_id": webhook_id,
                "status": "removed"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove webhook: {str(e)}")

@router.post("/send-alert")
async def send_compliance_alert(
    alert: ComplianceAlert,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Send immediate compliance alert"""
    try:
        user_id = current_user["sub"]
        user_webhooks = WEBHOOK_CONFIGURATIONS.get(user_id, [])
        
        alert_data = alert.dict()
        alert_data["timestamp"] = datetime.now().isoformat()
        alert_data["user_id"] = user_id
        
        # Send to all configured webhooks that match event type
        matching_webhooks = [
            w for w in user_webhooks 
            if w.get("active", True) and "compliance_violation" in w.get("events", [])
        ]
        
        if not matching_webhooks:
            return {
                "success": True,
                "data": {
                    "alert_sent": False,
                    "message": "No matching webhook configurations found"
                }
            }
        
        # Process notifications in background
        for webhook_config in matching_webhooks:
            background_tasks.add_task(process_notification, webhook_config, alert_data)
        
        return {
            "success": True,
            "data": {
                "alert_sent": True,
                "webhooks_triggered": len(matching_webhooks),
                "alert_id": f"alert_{uuid.uuid4().hex[:16]}"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")

@router.get("/notifications/history")
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    severity: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get notification history"""
    try:
        # Filter notifications (in production, use database queries)
        filtered_notifications = NOTIFICATION_HISTORY.copy()
        
        if severity:
            filtered_notifications = [n for n in filtered_notifications if n["severity"] == severity]
        
        # Sort by sent_at descending
        filtered_notifications.sort(key=lambda x: x["sent_at"], reverse=True)
        
        # Paginate
        paginated_notifications = filtered_notifications[offset:offset + limit]
        
        return {
            "success": True,
            "data": {
                "notifications": paginated_notifications,
                "total_count": len(filtered_notifications),
                "limit": limit,
                "offset": offset
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification history: {str(e)}")

@router.post("/test-webhook/{webhook_id}")
async def test_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Test a specific webhook configuration"""
    try:
        user_id = current_user["sub"]
        user_webhooks = WEBHOOK_CONFIGURATIONS.get(user_id, [])
        
        # Find webhook
        webhook_config = next((w for w in user_webhooks if w["id"] == webhook_id), None)
        if not webhook_config:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        test_alert = {
            "violation_type": "test_alert",
            "severity": "info",
            "table_name": "test_table",
            "column_name": "test_column",
            "description": "This is a test alert to verify webhook functionality",
            "recommendation": "No action required - this is a test",
            "project_id": "test_project"
        }
        
        # Send test notification
        await process_notification(webhook_config, test_alert)
        
        return {
            "success": True,
            "data": {
                "webhook_id": webhook_id,
                "test_sent": True,
                "message": "Test notification sent successfully"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test webhook: {str(e)}")

@router.get("/events")
async def get_available_events():
    """Get list of available events for webhook configuration"""
    try:
        events = [
            {
                "name": "compliance_violation",
                "description": "Triggered when a compliance violation is detected",
                "severity_levels": ["critical", "high", "medium", "low"]
            },
            {
                "name": "schema_change",
                "description": "Triggered when schema changes are detected",
                "severity_levels": ["high", "medium", "low"]
            },
            {
                "name": "audit_failure",
                "description": "Triggered when security audits fail",
                "severity_levels": ["critical", "high"]
            },
            {
                "name": "data_exposure",
                "description": "Triggered when potential data exposure is detected",
                "severity_levels": ["critical", "high", "medium"]
            },
            {
                "name": "access_violation",
                "description": "Triggered when unauthorized access attempts are detected",
                "severity_levels": ["critical", "high"]
            },
            {
                "name": "encryption_issue",
                "description": "Triggered when encryption problems are found",
                "severity_levels": ["critical", "high", "medium"]
            }
        ]
        
        return {
            "success": True,
            "data": {
                "events": events
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")

@router.get("/stats")
async def get_alert_stats():
    """Get compliance alert statistics"""
    try:
        # Calculate stats from notification history
        total_alerts = len(NOTIFICATION_HISTORY)
        
        if total_alerts == 0:
            return {
                "success": True,
                "data": {
                    "total_alerts": 0,
                    "alerts_by_severity": {},
                    "success_rate": 0,
                    "recent_alerts": []
                }
            }
        
        # Group by severity
        alerts_by_severity = {}
        successful_alerts = 0
        
        for notification in NOTIFICATION_HISTORY:
            severity = notification["severity"]
            alerts_by_severity[severity] = alerts_by_severity.get(severity, 0) + 1
            if notification["status"] == "sent":
                successful_alerts += 1
        
        success_rate = (successful_alerts / total_alerts) * 100
        
        # Get recent alerts (last 10)
        recent_alerts = sorted(NOTIFICATION_HISTORY, key=lambda x: x["sent_at"], reverse=True)[:10]
        
        return {
            "success": True,
            "data": {
                "total_alerts": total_alerts,
                "alerts_by_severity": alerts_by_severity,
                "success_rate": round(success_rate, 2),
                "successful_alerts": successful_alerts,
                "failed_alerts": total_alerts - successful_alerts,
                "recent_alerts": recent_alerts
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert stats: {str(e)}")
