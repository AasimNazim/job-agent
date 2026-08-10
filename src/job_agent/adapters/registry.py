from typing import Dict, Type
from .base import JobSourceAdapter

class AdapterRegistry:
    """
    Registry for ATS job adapters.
    Maps platform string (e.g., 'greenhouse') to its adapter class.
    """
    
    _adapters: Dict[str, Type[JobSourceAdapter]] = {}

    @classmethod
    def register(cls, platform: str, adapter_class: Type[JobSourceAdapter]) -> None:
        """
        Register a new adapter class for a given platform.
        """
        cls._adapters[platform.lower()] = adapter_class

    @classmethod
    def get_adapter(cls, platform: str) -> JobSourceAdapter:
        """
        Instantiate and return the correct adapter for the platform.
        """
        platform_key = platform.lower()
        if platform_key not in cls._adapters:
            raise ValueError(f"No adapter registered for platform: {platform}")
        
        adapter_class = cls._adapters[platform_key]
        return adapter_class()

    @classmethod
    def supported_platforms(cls) -> list[str]:
        """
        Return a list of all currently supported platforms.
        """
        return list(cls._adapters.keys())
