"""Test resource provider that mimics a storage volume."""
from typing import Any

from stackzilla.attribute.attribute import StackzillaAttribute
from stackzilla.provider.null.base import BaseNullResource


class Instance(BaseNullResource):
    """Dummy instance resource."""

    # This dynamic value will be set in the create() method
    ipv4_addr = StackzillaAttribute(dynamic=True)

    type = StackzillaAttribute(required=True, choices=['large', 'medium', 'small'])

    def __init__(self) -> None:
        """Default constructor that sets up logging."""
        super().__init__(provider_name='stackzilla.provider.null.instance')

    def create(self) -> None:
        """Create the null instance."""
        # Persist to the database
        super().create()

        # Set the dynamic value
        self.ipv4_addr = '192.168.1.1'

        # Re-save all of the attributes to the database
        super().update()

    def type_modified(self, previous_value: Any, new_value: Any) -> None:
        """Handle when the type is modified (does nothing but log a message)."""
        self._logger.debug(f'Modifying type from {previous_value} to {new_value}')
