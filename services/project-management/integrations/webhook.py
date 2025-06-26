import requests
from typing import Dict, Any, List
from .base import Integration

class WebhookIntegration(Integration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.enabled = config.get('enabled', True)
        self.webhooks: List[str] = config.get('webhooks', [])
        self.events: List[str] = config.get('events', [])

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def configure(self, config: Dict[str, Any]):
        self.webhooks = config.get('webhooks', self.webhooks)
        self.events = config.get('events', self.events)
        self.enabled = config.get('enabled', self.enabled)
        self.config = config

    def trigger(self, event: str, payload: Dict[str, Any]):
        if not self.enabled or event not in self.events:
            return
        for url in self.webhooks:
            try:
                resp = requests.post(url, json=payload, timeout=5)
                resp.raise_for_status()
            except Exception as e:
                print(f"[WebhookIntegration] Failed to POST to {url}: {e}")
                # TODO: Add proper logging/audit
