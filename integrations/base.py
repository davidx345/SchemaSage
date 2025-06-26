from abc import ABC, abstractmethod
from typing import Any, Dict

class Integration(ABC):
    """
    Base class for all integrations. Subclass this for each integration type.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def enable(self):
        pass

    @abstractmethod
    def disable(self):
        pass

    @abstractmethod
    def configure(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def trigger(self, event: str, payload: Dict[str, Any]):
        pass
