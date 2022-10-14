"""Exceptions for the diff module."""
import typing
from typing import List

if typing.TYPE_CHECKING:
    from stackzilla.diff.diff import AttributeModified

class UnhandledAttributeModifications(Exception):
    """Raised when a resource does not handle attribute modifications."""

    def __init__(self, unhandled_attributes: List['AttributeModified'], *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)
        self.unhandled_attributes = unhandled_attributes

class NoDiffError(Exception):
    """Raised when the results parameter is accessed prior to a diff operation being applied."""