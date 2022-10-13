"""Test resource provider that mimics a storage volume."""
from typing import List

from stackbot.attribute.attribute import StackBotAttribute
from stackbot.logging.provider import ProviderLogger
from stackbot.resource.base import ResourceVersion, StackBotResource


class Volume(StackBotResource):
    """Dummy volume resource."""

    format = StackBotAttribute(required=False, choices=['xfs', 'hdfs', 'fat'], default='xfs')
    size = StackBotAttribute(required=True)

    def __init__(self) -> None:
        """Default constructor that sets up logging."""
        super().__init__()
        self._logger = ProviderLogger(provider_name='stackbot-test:volume', resource_name=self.path())

    def create(self) -> None:
        """Called when the resource is created."""
        self._logger.debug(message="Creating volume")
        return super().create()

    def depends_on(self) -> List['StackBotResource']:
        """Required to be overridden."""

    @classmethod
    def version(cls) -> ResourceVersion:
        """Fetch the version of the resource provider."""
        return ResourceVersion(major=1, minor=0, build=0, name='FCS')
