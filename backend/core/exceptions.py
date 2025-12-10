"""Custom exceptions for the application domain layer."""


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str | None = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        if resource_id:
            message = f"{resource_type} with ID {resource_id} not found"
        else:
            message = f"{resource_type} not found"
        super().__init__(message)


class InvalidStateError(Exception):
    """Raised when an operation is attempted on a resource in an invalid state."""
    pass


class ValidationError(Exception):
    """Raised when validation fails."""
    pass
