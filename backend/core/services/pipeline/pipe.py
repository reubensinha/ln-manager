## Object that is Ordered list of stages that make up a pipeline

from collections.abc import Callable

from backend.core.services.pipeline.stage import Stage


class Pipe:
    """Pipeline composed of ordered stages.

    Data is passed sequentially through each stage, with each stage
    potentially modifying the data before passing it to the next.
    """

    def __init__(self, stages: list[Stage] | None = None):
        self.stages: list[Stage] = stages if stages is not None else []
    
    def __str__(self) -> str:
        # TODO: Improve print representation
        stage_names = [stage.name for stage in self.stages]
        return f"Pipe(stages={stage_names})"

    # TODO: Add method to return Pipleline as dict(?) for serialization
    
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

    def run_condition(self, data: dict) -> bool:
        """Determine if pipeline should execute.

        Override this method in subclasses to add custom execution guards.

        Args:
            data: The data that would be passed through the pipeline

        Returns:
            bool: True to execute pipeline, False to skip
        """
        return True

    async def execute(
        self, data: dict, condition: Callable[[dict], bool] | None = None
    ) -> dict:
        """Execute all stages in pipeline sequentially if condition is met.

        Args:
            data: Initial data to pass through the pipeline
            condition: Optional callable(data) -> bool to override run_condition()

        Returns:
            dict: Data after passing through all stages, or original data with
                  _pipeline_skipped flag if condition was not met
        """
        # Use provided condition or fall back to instance method
        check = condition if condition is not None else self.run_condition

        if not check(data):
            data["_pipeline_skipped"] = True
            return data

        current_data = data
        for stage in self.stages:
            current_data = await stage.execute(current_data)
        return current_data
