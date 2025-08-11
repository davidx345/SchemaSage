"""
Notification Service - Alert and notification delivery
"""
from typing import Dict
import json
import logging

from ...models.monitoring import (
    Alert, MonitoringRule, NotificationTemplate, NotificationChannel
)
from ...utils.logging import get_logger

logger = get_logger(__name__)

class NotificationService:
    """Notification delivery service."""
    
    def __init__(self):
        self.templates: Dict[str, NotificationTemplate] = {}
    
    async def send_alert_notifications(self, alert: Alert, rule: MonitoringRule):
        """Send notifications for an alert."""
        
        for channel in rule.notification_channels:
            try:
                await self._send_notification(channel, alert, rule, "alert")
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")
    
    async def send_resolution_notification(self, alert: Alert, rule: MonitoringRule):
        """Send notification when alert is resolved."""
        
        for channel in rule.notification_channels:
            try:
                await self._send_notification(channel, alert, rule, "resolution")
            except Exception as e:
                logger.error(f"Failed to send resolution notification via {channel}: {e}")
    
    async def _send_notification(
        self, 
        channel: NotificationChannel, 
        alert: Alert, 
        rule: MonitoringRule,
        notification_type: str
    ):
        """Send notification via specific channel."""
        
        if channel == NotificationChannel.EMAIL:
            await self._send_email_notification(alert, rule, notification_type)
        elif channel == NotificationChannel.SLACK:
            await self._send_slack_notification(alert, rule, notification_type)
        elif channel == NotificationChannel.WEBHOOK:
            await self._send_webhook_notification(alert, rule, notification_type)
        else:
            logger.warning(f"Notification channel {channel} not implemented")
    
    async def _send_email_notification(
        self, 
        alert: Alert, 
        rule: MonitoringRule, 
        notification_type: str
    ):
        """Send email notification."""
        
        # In a real implementation, this would integrate with an email service
        subject = f"[{alert.severity.upper()}] {alert.title}"
        body = f"""
        Alert Details:
        - Rule: {rule.name}
        - Description: {alert.description}
        - Severity: {alert.severity}
        - Triggered At: {alert.triggered_at}
        - Current Value: {alert.trigger_value}
        - Threshold: {alert.threshold_value}
        """
        
        logger.info(f"EMAIL: {subject}\n{body}")
    
    async def _send_slack_notification(
        self, 
        alert: Alert, 
        rule: MonitoringRule, 
        notification_type: str
    ):
        """Send Slack notification."""
        
        # In a real implementation, this would integrate with Slack API
        message = {
            "text": f"{alert.severity.upper()}: {alert.title}",
            "attachments": [
                {
                    "color": "danger" if alert.severity in ["high", "critical"] else "warning",
                    "fields": [
                        {"title": "Rule", "value": rule.name, "short": True},
                        {"title": "Current Value", "value": str(alert.trigger_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold_value), "short": True},
                        {"title": "Time", "value": alert.triggered_at.isoformat(), "short": True}
                    ]
                }
            ]
        }
        
        logger.info(f"SLACK: {json.dumps(message, indent=2)}")
    
    async def _send_webhook_notification(
        self, 
        alert: Alert, 
        rule: MonitoringRule, 
        notification_type: str
    ):
        """Send webhook notification."""
        
        # In a real implementation, this would make HTTP requests to webhook URLs
        payload = {
            "alert_id": alert.alert_id,
            "rule_id": rule.rule_id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "current_value": alert.trigger_value,
            "threshold": alert.threshold_value,
            "triggered_at": alert.triggered_at.isoformat(),
            "notification_type": notification_type
        }
        
        logger.info(f"WEBHOOK: {json.dumps(payload, indent=2)}")
