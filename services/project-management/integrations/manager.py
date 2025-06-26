import importlib
from typing import Dict, Type, Any
from .base import Integration

class IntegrationManager:
    """
    Loads and manages all integrations.
    """
    def __init__(self):
        self.integrations: Dict[str, Integration] = {}

    def register(self, name: str, integration_cls: Type[Integration], config: Dict[str, Any]):
        self.integrations[name] = integration_cls(config)

    def enable(self, name: str):
        if name in self.integrations:
            self.integrations[name].enable()

    def disable(self, name: str):
        if name in self.integrations:
            self.integrations[name].disable()

    def configure(self, name: str, config: Dict[str, Any]):
        if name in self.integrations:
            self.integrations[name].configure(config)

    def trigger(self, name: str, event: str, payload: Dict[str, Any]):
        if name in self.integrations:
            self.integrations[name].trigger(event, payload)
