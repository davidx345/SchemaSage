import requests
from typing import Dict, Any, List
from .base import Integration

class NotificationIntegration(Integration):
    """
    Sends notifications to Slack, Microsoft Teams, or Gmail.
    Config example:
    {
        "enabled": True,
        "channels": [
            {"type": "slack", "webhook_url": "..."},
            {"type": "teams", "webhook_url": "..."},
            {"type": "gmail", "email": "..."}
        ],
        "events": ["schema_change", "data_issue"]
    }
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.enabled = config.get('enabled', True)
        self.channels: List[Dict[str, Any]] = config.get('channels', [])
        self.events: List[str] = config.get('events', [])

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def configure(self, config: Dict[str, Any]):
        self.channels = config.get('channels', self.channels)
        self.events = config.get('events', self.events)
        self.enabled = config.get('enabled', self.enabled)
        self.config = config

    def trigger(self, event: str, payload: Dict[str, Any]):
        if not self.enabled or event not in self.events:
            return
        for channel in self.channels:
            try:
                if channel['type'] == 'slack' or channel['type'] == 'teams':
                    requests.post(channel['webhook_url'], json=payload, timeout=5)
                elif channel['type'] == 'gmail':
                    # For demo: just print, real impl would use SMTP or Gmail API
                    print(f"Send email to {channel['email']}: {payload}")
            except Exception as e:
                print(f"[NotificationIntegration] Failed to notify {channel}: {e}")
