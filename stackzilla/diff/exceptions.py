"""Exceptions for the diff module."""
import typing
from typing import List

if typing.TYPE_CHECKING:
    from stackzilla.diff.diff import AttributeModified

class VersionIncompatibility(Exception):
    """Raised when the major version of two resources do not match."""

class UnhandledAttributeModifications(Exception):
    """Raised when a resource does not handle attribute modifications."""

    def __init__(self, unhandled_attributes: List['AttributeModified'], *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)
        self.unhandled_attributes = unhandled_attributes

class NoDiffError(Exception):
    """Raised when the results parameter is accessed prior to a diff operation being applied."""

class ApplyErrors(Exception):
    """Exception that is raised if there are errors durring apply."""

    def __init__(self, errors: List[str], *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)
        self.errors = errors
