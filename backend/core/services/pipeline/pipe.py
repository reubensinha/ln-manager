## Object that is Ordered list of stages that make up a pipeline



from backend.core.services.pipeline.stage import Stage
from typing import Optional


class Pipe():
    """Pipeline composed of ordered stages.
    
    Data is passed sequentially through each stage, with each stage
    potentially modifying the data before passing it to the next.
    """
    def __init__(self, stages: Optional[list[Stage]] = None):
        self.stages: list[Stage] = stages if stages is not None else []
        
    def add_stage(self, stage: Stage):
        """Add stage to end of pipeline."""
        self.stages.append(stage)
        
    def remove_stage_name(self, name: str) -> bool:
        """Remove stage from pipeline by name.
        
        Args:
            name: Name of the stage to remove
            
        Returns:
            bool: True if stage was found and removed, False otherwise
        """
        for i, stage in enumerate(self.stages):
            if stage.name == name:
                self.stages.pop(i)
                return True
        return False
    
    def remove_stage_index(self, index: int):
        """Remove stage from pipeline by index.
        
        Args:
            index: Index of the stage to remove
        """
        if 0 <= index < len(self.stages):
            self.stages.pop(index)
    
    def insert_stage(self, index: int, stage: Stage):
        """Insert stage into pipeline at specified index.
        
        Args:
            index: Position to insert the stage
            stage: Stage to insert
        """
        self.stages.insert(index, stage)
    
    async def execute(self, data: dict) -> dict:
        """Execute all stages in pipeline sequentially.
        
        Args:
            data: Initial data to pass through the pipeline
            
        Returns:
            dict: Data after passing through all stages
        """
        current_data = data
        for stage in self.stages:
            current_data = await stage.execute(current_data)
        return current_data
