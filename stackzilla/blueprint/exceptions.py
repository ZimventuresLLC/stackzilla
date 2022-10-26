"""Exceptions for the blueprint module."""
from typing import List

from stackzilla.resource.exceptions import ResourceVerifyError


class BlueprintVerifyFailure(Exception):
    """Raised when a blueprint fails to verify."""

    def __init__(self, errors: List[ResourceVerifyError], *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)
        self.errors = errors

class ResourceNotFound(Exception):
    """Raised when a resource is not found within the blueprint."""
