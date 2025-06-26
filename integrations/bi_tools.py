from typing import Dict, Any, List
from .base import Integration

class BIToolsIntegration(Integration):
    """
    Handles pushing schema/lineage to BI tools (Tableau, Power BI).
    Config example:
    {
        "enabled": True,
        "tools": [
            {"type": "tableau", "api_url": "...", "api_key": "..."},
            {"type": "powerbi", "workspace_id": "...", "access_token": "..."}
        ]
    }
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.enabled = config.get('enabled', True)
        self.tools: List[Dict[str, Any]] = config.get('tools', [])

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def configure(self, config: Dict[str, Any]):
        self.tools = config.get('tools', self.tools)
        self.enabled = config.get('enabled', self.enabled)
        self.config = config

    def trigger(self, event: str, payload: Dict[str, Any]):
        if not self.enabled:
            return
        # For demo: just print, real impl would use Tableau/Power BI APIs
        for tool in self.tools:
            print(f"[BIToolsIntegration] Would push {event} to {tool['type']} with payload: {payload}")
