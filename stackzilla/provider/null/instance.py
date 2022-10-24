"""Test resource provider that mimics a storage volume."""
from typing import List

from stackzilla.attribute.attribute import StackzillaAttribute
from stackzilla.logging.provider import ProviderLogger
from stackzilla.resource.base import ResourceVersion, StackzillaResource
from stackzilla.resource.exceptions import ResourceCreateFailure


class Instance(StackzillaResource):
    """Dummy instance resource."""

    type = StackzillaAttribute(required=True, choices=['large', 'medium', 'small'])
    create_failure = False
    def __init__(self) -> None:
        """Default constructor that sets up logging."""
        super().__init__()
        self._logger = ProviderLogger(provider_name='stackzilla-test:volume', resource_name=self.path())

    def create(self) -> None:
        """Called when the resource is created."""
        self._logger.debug(message="Creating volume")

        if self.create_failure:
            raise ResourceCreateFailure(resource_name=self.path(), reason="tesing failure")

        return super().create()

    def depends_on(self) -> List['StackzillaResource']:
        """Required to be overridden."""
        return []

    @classmethod
    def version(cls) -> ResourceVersion:
        """Fetch the version of the resource provider."""
        return ResourceVersion(major=1, minor=0, build=0, name='FCS')
