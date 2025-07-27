"""
Alerting and notification system
"""
import asyncio
import logging
import json
import smtplib
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aiohttp

from .base import Alert, AlertSeverity, Metric
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)

class AlertRule:
    """Defines an alert rule"""
    
    def __init__(
        self,
        name: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        description: str = "",
        notification_channels: List[str] = None
    ):
        self.name = name
        self.metric_name = metric_name
        self.condition = condition  # >, <, >=, <=, ==, !=
        self.threshold = threshold
        self.severity = severity
        self.description = description
        self.notification_channels = notification_channels or []
        self.enabled = True
        self.cooldown_minutes = 15  # Minimum time between alerts
        self.last_triggered = None
    
    def evaluate(self, current_value: float) -> bool:
        """Evaluate if the alert condition is met"""
        if not self.enabled:
            return False
        
        # Check cooldown
        if self.last_triggered:
            cooldown_time = self.last_triggered + timedelta(minutes=self.cooldown_minutes)
            if datetime.now() < cooldown_time:
                return False
        
        # Evaluate condition
        if self.condition == ">":
            return current_value > self.threshold
        elif self.condition == "<":
            return current_value < self.threshold
        elif self.condition == ">=":
            return current_value >= self.threshold
        elif self.condition == "<=":
            return current_value <= self.threshold
        elif self.condition == "==":
            return current_value == self.threshold
        elif self.condition == "!=":
            return current_value != self.threshold
        else:
            logger.warning(f"Unknown condition: {self.condition}")
            return False


class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = True
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for alert"""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send email notification"""
        try:
            smtp_server = self.config.get('smtp_server')
            smtp_port = self.config.get('smtp_port', 587)
            username = self.config.get('username')
            password = self.config.get('password')
            from_email = self.config.get('from_email')
            to_emails = self.config.get('to_emails', [])
            
            if not all([smtp_server, username, password, from_email, to_emails]):
                logger.error("Email configuration incomplete")
                return False
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.name}"
            
            # Email body
            body = f"""
Alert: {alert.name}
Severity: {alert.severity.value.upper()}
Description: {alert.description}
Metric: {alert.metric_name}
Condition: {alert.condition} {alert.threshold}
Current Value: {alert.current_value}
Triggered At: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}

Alert ID: {alert.alert_id}
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            text = msg.as_string()
            server.sendmail(from_email, to_emails, text)
            server.quit()
            
            logger.info(f"Email alert sent for {alert.name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel"""
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send webhook notification"""
        try:
            webhook_url = self.config.get('webhook_url')
            headers = self.config.get('headers', {})
            
            if not webhook_url:
                logger.error("Webhook URL not configured")
                return False
            
            # Prepare payload
            payload = {
                'alert_id': alert.alert_id,
                'name': alert.name,
                'description': alert.description,
                'severity': alert.severity.value,
                'metric_name': alert.metric_name,
                'condition': alert.condition,
                'threshold': alert.threshold,
                'current_value': alert.current_value,
                'triggered_at': alert.triggered_at.isoformat(),
                'tags': alert.tags
            }
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent for {alert.name}")
                        return True
                    else:
                        logger.error(f"Webhook failed with status {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send Slack notification"""
        try:
            webhook_url = self.config.get('webhook_url')
            channel = self.config.get('channel', '#alerts')
            username = self.config.get('username', 'SchemaSage')
            
            if not webhook_url:
                logger.error("Slack webhook URL not configured")
                return False
            
            # Color based on severity
            color_map = {
                AlertSeverity.INFO: '#36a64f',      # green
                AlertSeverity.WARNING: '#ffeb3b',   # yellow
                AlertSeverity.ERROR: '#ff9800',     # orange
                AlertSeverity.CRITICAL: '#f44336'   # red
            }
            
            color = color_map.get(alert.severity, '#36a64f')
            
            # Prepare Slack payload
            payload = {
                'channel': channel,
                'username': username,
                'icon_emoji': ':warning:',
                'attachments': [{
                    'color': color,
                    'title': f"{alert.severity.value.upper()}: {alert.name}",
                    'text': alert.description,
                    'fields': [
                        {
                            'title': 'Metric',
                            'value': alert.metric_name,
                            'short': True
                        },
                        {
                            'title': 'Condition',
                            'value': f"{alert.condition} {alert.threshold}",
                            'short': True
                        },
                        {
                            'title': 'Current Value',
                            'value': str(alert.current_value),
                            'short': True
                        },
                        {
                            'title': 'Triggered At',
                            'value': alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'short': True
                        }
                    ],
                    'footer': 'SchemaSage Monitoring',
                    'ts': int(alert.triggered_at.timestamp())
                }]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent for {alert.name}")
                        return True
                    else:
                        logger.error(f"Slack webhook failed with status {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_history_size = 1000
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel"""
        self.notification_channels[channel.name] = channel
        logger.info(f"Added notification channel: {channel.name}")
    
    async def evaluate_alerts(self):
        """Evaluate all alert rules against current metrics"""
        for rule_name, rule in self.alert_rules.items():
            try:
                # Get latest metric value
                latest_metric = self.metrics_collector.get_latest_metric(rule.metric_name)
                
                if latest_metric is None:
                    continue
                
                current_value = latest_metric.value
                
                # Evaluate alert condition
                if rule.evaluate(current_value):
                    await self._trigger_alert(rule, current_value, latest_metric)
                else:
                    # Check if alert should be resolved
                    await self._resolve_alert(rule_name)
            
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule_name}: {e}")
    
    async def _trigger_alert(self, rule: AlertRule, current_value: float, metric: Metric):
        """Trigger an alert"""
        alert_id = f"{rule.name}_{int(datetime.now().timestamp())}"
        
        alert = Alert(
            alert_id=alert_id,
            name=rule.name,
            description=rule.description,
            severity=rule.severity,
            metric_name=rule.metric_name,
            condition=rule.condition,
            threshold=rule.threshold,
            current_value=current_value,
            tags=metric.tags,
            notification_channels=rule.notification_channels
        )
        
        # Add to active alerts
        self.active_alerts[rule.name] = alert
        
        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history_size:
            self.alert_history = self.alert_history[-self.max_history_size:]
        
        # Update rule last triggered time
        rule.last_triggered = datetime.now()
        
        # Send notifications
        await self._send_notifications(alert)
        
        logger.warning(f"Alert triggered: {alert.name} - {alert.description}")
    
    async def _resolve_alert(self, rule_name: str):
        """Resolve an active alert"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = "resolved"
            alert.resolved_at = datetime.now()
            
            # Remove from active alerts
            del self.active_alerts[rule_name]
            
            logger.info(f"Alert resolved: {alert.name}")
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert"""
        for channel_name in alert.notification_channels:
            if channel_name in self.notification_channels:
                channel = self.notification_channels[channel_name]
                if channel.enabled:
                    try:
                        success = await channel.send_notification(alert)
                        if not success:
                            logger.error(f"Failed to send notification via {channel_name}")
                    except Exception as e:
                        logger.error(f"Error sending notification via {channel_name}: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)
        
        # Count by severity
        severity_counts = {}
        for alert in self.alert_history:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_count,
            'severity_breakdown': severity_counts,
            'alert_rules_count': len(self.alert_rules),
            'notification_channels_count': len(self.notification_channels)
        }
