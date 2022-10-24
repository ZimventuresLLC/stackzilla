"""Test resource provider that mimics a storage volume."""
from stackzilla.attribute.attribute import StackzillaAttribute
from stackzilla.provider.null.base import BaseNullResource


class Instance(BaseNullResource):
    """Dummy instance resource."""

    type = StackzillaAttribute(required=True, choices=['large', 'medium', 'small'])

    def __init__(self) -> None:
        """Default constructor that sets up logging."""
        super().__init__(provider_name='stackzilla.provider.null.instance')
