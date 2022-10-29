"""Test resource provider that mimics a storage volume."""
from typing import Any

from stackzilla.attribute.attribute import StackzillaAttribute
from stackzilla.provider.null.base import BaseNullResource


class Instance(BaseNullResource):
    """Dummy instance resource."""

    type = StackzillaAttribute(required=True, choices=['large', 'medium', 'small'])

    def __init__(self) -> None:
        """Default constructor that sets up logging."""
        super().__init__(provider_name='stackzilla.provider.null.instance')

    def type_modified(self, previous_value: Any, new_value: Any) -> None:
        """Handle when the type is modified (does nothing but log a message)."""
        self._logger.debug(f'Modifying type from {previous_value} to {new_value}')
