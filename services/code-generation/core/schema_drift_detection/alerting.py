"""
Alert system for schema drift notifications
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from .models import DriftAlert, AlertChannel, SchemaChange, ChangeSeverity

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alerts for schema drift detection
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize alert manager
        
        Args:
            config: Alert configuration containing channel settings
        """
        self.config = config or {}
        self.alert_handlers = {
            AlertChannel.EMAIL: self._send_email_alert,
            AlertChannel.SLACK: self._send_slack_alert,
            AlertChannel.WEBHOOK: self._send_webhook_alert,
            AlertChannel.SMS: self._send_sms_alert,
            AlertChannel.DISCORD: self._send_discord_alert
        }
        self.custom_handlers: List[Callable[[DriftAlert], None]] = []
    
    async def send_alert(self, alert: DriftAlert):
        """
        Send alert through all configured channels
        
        Args:
            alert: Alert to send
        """
        logger.info(f"Sending alert {alert.alert_id} through {len(alert.channels)} channels")
        
        # Send through built-in channels
        for channel in alert.channels:
            if channel in self.alert_handlers:
                try:
                    await self.alert_handlers[channel](alert)
                    logger.info(f"Alert sent via {channel.value}")
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel.value}: {e}")
        
        # Send through custom handlers
        for handler in self.custom_handlers:
            try:
                await asyncio.create_task(self._run_custom_handler(handler, alert))
            except Exception as e:
                logger.error(f"Custom alert handler failed: {e}")
    
    async def _run_custom_handler(self, handler: Callable, alert: DriftAlert):
        """Run custom handler in async context"""
        if asyncio.iscoroutinefunction(handler):
            await handler(alert)
        else:
            handler(alert)
    
    async def _send_email_alert(self, alert: DriftAlert):
        """Send alert via email"""
        email_config = self.config.get('email', {})
        if not email_config:
            logger.warning("Email configuration not found")
            return
        
        # Prepare email content
        subject = f"Schema Drift Alert - {alert.severity.value.upper()}"
        body = self._format_email_body(alert)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_config.get('from_address')
        msg['To'] = ', '.join(email_config.get('recipients', []))
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        try:
            with smtplib.SMTP(email_config.get('smtp_host'), email_config.get('smtp_port', 587)) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                
                if email_config.get('username') and email_config.get('password'):
                    server.login(email_config['username'], email_config['password'])
                
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    async def _send_slack_alert(self, alert: DriftAlert):
        """Send alert via Slack webhook"""
        slack_config = self.config.get('slack', {})
        webhook_url = slack_config.get('webhook_url')
        
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Format Slack message
        message = self._format_slack_message(alert)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=message) as response:
                if response.status != 200:
                    raise Exception(f"Slack API returned status {response.status}")
    
    async def _send_webhook_alert(self, alert: DriftAlert):
        """Send alert via generic webhook"""
        webhook_config = self.config.get('webhook', {})
        webhook_url = webhook_config.get('url')
        
        if not webhook_url:
            logger.warning("Webhook URL not configured")
            return
        
        # Prepare webhook payload
        payload = {
            'alert_id': alert.alert_id,
            'severity': alert.severity.value,
            'message': alert.message,
            'triggered_at': alert.triggered_at.isoformat(),
            'changes': [change.to_dict() for change in alert.changes],
            'metadata': {
                'change_count': len(alert.changes),
                'severity_breakdown': self._get_severity_breakdown(alert.changes)
            }
        }
        
        headers = webhook_config.get('headers', {})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, headers=headers) as response:
                if response.status not in [200, 201, 202]:
                    raise Exception(f"Webhook returned status {response.status}")
    
    async def _send_sms_alert(self, alert: DriftAlert):
        """Send alert via SMS (placeholder implementation)"""
        sms_config = self.config.get('sms', {})
        
        if not sms_config:
            logger.warning("SMS configuration not found")
            return
        
        # This would integrate with SMS providers like Twilio, AWS SNS, etc.
        logger.info(f"SMS alert would be sent: {alert.message}")
    
    async def _send_discord_alert(self, alert: DriftAlert):
        """Send alert via Discord webhook"""
        discord_config = self.config.get('discord', {})
        webhook_url = discord_config.get('webhook_url')
        
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return
        
        # Format Discord embed
        embed = self._format_discord_embed(alert)
        message = {'embeds': [embed]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=message) as response:
                if response.status not in [200, 204]:
                    raise Exception(f"Discord API returned status {response.status}")
    
    def _format_email_body(self, alert: DriftAlert) -> str:
        """Format email body with HTML"""
        severity_colors = {
            ChangeSeverity.LOW: '#28a745',
            ChangeSeverity.MEDIUM: '#ffc107',
            ChangeSeverity.HIGH: '#fd7e14',
            ChangeSeverity.CRITICAL: '#dc3545'
        }
        
        color = severity_colors.get(alert.severity, '#6c757d')
        
        html = f"""
        <html>
        <body>
            <h2 style="color: {color};">Schema Drift Alert - {alert.severity.value.upper()}</h2>
            <p><strong>Alert ID:</strong> {alert.alert_id}</p>
            <p><strong>Triggered At:</strong> {alert.triggered_at}</p>
            <p><strong>Message:</strong> {alert.message}</p>
            
            <h3>Changes Detected ({len(alert.changes)}):</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f8f9fa;">
                    <th>Change Type</th>
                    <th>Object</th>
                    <th>Severity</th>
                    <th>Details</th>
                </tr>
        """
        
        for change in alert.changes:
            html += f"""
                <tr>
                    <td>{change.change_type.value}</td>
                    <td>{change.object_name}</td>
                    <td style="color: {severity_colors.get(change.severity, '#6c757d')};">
                        {change.severity.value}
                    </td>
                    <td>{change.details}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    def _format_slack_message(self, alert: DriftAlert) -> Dict[str, Any]:
        """Format Slack message"""
        severity_colors = {
            ChangeSeverity.LOW: 'good',
            ChangeSeverity.MEDIUM: 'warning',
            ChangeSeverity.HIGH: 'danger',
            ChangeSeverity.CRITICAL: 'danger'
        }
        
        color = severity_colors.get(alert.severity, 'good')
        
        # Create fields for each change
        fields = []
        for change in alert.changes[:10]:  # Limit to 10 changes to avoid message limits
            fields.append({
                'title': change.change_type.value.replace('_', ' ').title(),
                'value': f"{change.object_name}\n*Severity:* {change.severity.value}",
                'short': True
            })
        
        if len(alert.changes) > 10:
            fields.append({
                'title': 'Additional Changes',
                'value': f"... and {len(alert.changes) - 10} more changes",
                'short': False
            })
        
        return {
            'attachments': [{
                'color': color,
                'title': f'Schema Drift Alert - {alert.severity.value.upper()}',
                'text': alert.message,
                'fields': fields,
                'footer': 'SchemaSage',
                'ts': int(alert.triggered_at.timestamp())
            }]
        }
    
    def _format_discord_embed(self, alert: DriftAlert) -> Dict[str, Any]:
        """Format Discord embed"""
        severity_colors = {
            ChangeSeverity.LOW: 0x28a745,
            ChangeSeverity.MEDIUM: 0xffc107,
            ChangeSeverity.HIGH: 0xfd7e14,
            ChangeSeverity.CRITICAL: 0xdc3545
        }
        
        color = severity_colors.get(alert.severity, 0x6c757d)
        
        # Create fields for changes
        fields = []
        change_summary = self._get_change_type_summary(alert.changes)
        
        for change_type, count in change_summary.items():
            if count > 0:
                fields.append({
                    'name': change_type.replace('_', ' ').title(),
                    'value': str(count),
                    'inline': True
                })
        
        embed = {
            'title': f'Schema Drift Alert - {alert.severity.value.upper()}',
            'description': alert.message,
            'color': color,
            'fields': fields,
            'footer': {
                'text': 'SchemaSage'
            },
            'timestamp': alert.triggered_at.isoformat()
        }
        
        return embed
    
    def _get_severity_breakdown(self, changes: List[SchemaChange]) -> Dict[str, int]:
        """Get breakdown of changes by severity"""
        breakdown = {}
        for severity in ChangeSeverity:
            breakdown[severity.value] = 0
        
        for change in changes:
            breakdown[change.severity.value] += 1
        
        return breakdown
    
    def _get_change_type_summary(self, changes: List[SchemaChange]) -> Dict[str, int]:
        """Get summary of changes by type"""
        summary = {}
        for change in changes:
            change_type = change.change_type.value
            summary[change_type] = summary.get(change_type, 0) + 1
        
        return summary
    
    def add_custom_handler(self, handler: Callable[[DriftAlert], None]):
        """Add custom alert handler"""
        self.custom_handlers.append(handler)
    
    def remove_custom_handler(self, handler: Callable[[DriftAlert], None]):
        """Remove custom alert handler"""
        if handler in self.custom_handlers:
            self.custom_handlers.remove(handler)


class AlertFilter:
    """
    Filters alerts based on rules to reduce noise
    """
    
    def __init__(self, rules: List[Dict[str, Any]] = None):
        """
        Initialize alert filter
        
        Args:
            rules: List of filtering rules
        """
        self.rules = rules or []
    
    def should_send_alert(self, alert: DriftAlert) -> bool:
        """
        Check if alert should be sent based on filtering rules
        
        Args:
            alert: Alert to check
            
        Returns:
            True if alert should be sent
        """
        for rule in self.rules:
            if not self._evaluate_rule(alert, rule):
                return False
        
        return True
    
    def _evaluate_rule(self, alert: DriftAlert, rule: Dict[str, Any]) -> bool:
        """Evaluate a single filtering rule"""
        rule_type = rule.get('type')
        
        if rule_type == 'severity_threshold':
            threshold = ChangeSeverity(rule.get('threshold', 'low'))
            severity_order = [ChangeSeverity.LOW, ChangeSeverity.MEDIUM, ChangeSeverity.HIGH, ChangeSeverity.CRITICAL]
            return severity_order.index(alert.severity) >= severity_order.index(threshold)
        
        elif rule_type == 'change_count_threshold':
            threshold = rule.get('threshold', 1)
            return len(alert.changes) >= threshold
        
        elif rule_type == 'excluded_change_types':
            excluded_types = set(rule.get('change_types', []))
            alert_types = {change.change_type.value for change in alert.changes}
            return not alert_types.issubset(excluded_types)
        
        elif rule_type == 'time_based':
            # Implement time-based filtering (e.g., only during business hours)
            return True
        
        # Default to allowing the alert
        return True
    
    def add_rule(self, rule: Dict[str, Any]):
        """Add filtering rule"""
        self.rules.append(rule)
    
    def remove_rule(self, rule: Dict[str, Any]):
        """Remove filtering rule"""
        if rule in self.rules:
            self.rules.remove(rule)
