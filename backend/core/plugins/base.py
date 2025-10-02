from abc import ABC, abstractmethod
from typing import Any

class BasePlugin(ABC):
    """Base interface for all plugins."""

    name: str
    version: str
    description: str = ""

    def __init__(self, **kwargs: Any):
        # Allow plugins to receive config from DB or user settings
        for k, v in kwargs.items():
            setattr(self, k, v)

    @abstractmethod
    def start(self) -> None:
        """Called when the plugin is loaded and ready."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Called when the plugin is unloaded or disabled."""
        ...
