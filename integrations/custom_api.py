import requests
from typing import Dict, Any, List
from .base import Integration

class CustomAPIIntegration(Integration):
    """
    Handles user-defined API connectors for custom workflows.
    Config example:
    {
        "enabled": True,
        "connectors": [
            {
                "name": "MyInternalAPI",
                "url": "https://api.example.com/endpoint",
                "method": "POST",
                "headers": {"Authorization": "Bearer ..."},
                "payload_template": {"field": "{{value}}"}
            }
        ]
    }
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.enabled = config.get('enabled', True)
        self.connectors: List[Dict[str, Any]] = config.get('connectors', [])

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def configure(self, config: Dict[str, Any]):
        self.connectors = config.get('connectors', self.connectors)
        self.enabled = config.get('enabled', self.enabled)
        self.config = config

    def trigger(self, event: str, payload: Dict[str, Any]):
        if not self.enabled:
            return
        for connector in self.connectors:
            try:
                url = connector['url']
                method = connector.get('method', 'POST').upper()
                headers = connector.get('headers', {})
                # For demo: just send the payload as-is; in real use, render template
                if method == 'POST':
                    requests.post(url, json=payload, headers=headers, timeout=5)
                elif method == 'PUT':
                    requests.put(url, json=payload, headers=headers, timeout=5)
                elif method == 'GET':
                    requests.get(url, params=payload, headers=headers, timeout=5)
                else:
                    print(f"[CustomAPIIntegration] Unsupported method: {method}")
            except Exception as e:
                print(f"[CustomAPIIntegration] Failed to call {connector['name']}: {e}")
