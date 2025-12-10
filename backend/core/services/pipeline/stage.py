## Object that is a stage in a pipeline

from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Optional


class Stage():
    """Represents a single stage in a pipeline.
    
    Each stage has a name and an async execute function that processes data.
    """
    def __init__(self, name: str, execute_fn: Optional[Callable[[dict], Awaitable[dict]]] = None):
        self.name = name
        self._execute_fn = execute_fn
    
    async def execute(self, data: dict) -> dict:
        """Execute the stage with the provided data.
        
        Args:
            data: Dictionary containing the pipeline data
            
        Returns:
            dict: Modified data to be passed to the next stage
        """
        if self._execute_fn:
            return await self._execute_fn(data)
        return data
        
    