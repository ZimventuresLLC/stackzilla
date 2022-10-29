"""Base boilerplate for NULL resources."""
from typing import Any, List

from stackzilla.attribute.attribute import StackzillaAttribute
from stackzilla.logger.provider import ProviderLogger
from stackzilla.resource.base import ResourceVersion, StackzillaResource
from stackzilla.resource.exceptions import (AttributeModifyFailure,
                                            ResourceCreateFailure)


class BaseNullResource(StackzillaResource):
    """Base boilerplate for NULL resources."""

    create_failure = False

    # When this attribute is modified, an exception will be raised in its on_modified() handler!
    mod_fail = StackzillaAttribute(default='modify at y0ur own perilz!')

    def __init__(self, provider_name: str) -> None:
        """Create the logger."""
        super().__init__()
        self._logger = ProviderLogger(provider_name=provider_name, resource_name=self.path())

    def create(self) -> None:
        """Called when the resource is created."""
        self._logger.debug(message="Creating")

        if self.create_failure:
            raise ResourceCreateFailure(resource_name=self.path(True), reason="tesing failure")

        return super().create()

    def delete(self) -> None:
        """Delete the resource from the database."""
        self._logger.debug(message="Deleting")
        super().delete()

    def depends_on(self) -> List['StackzillaResource']:
        """Required to be overridden."""
        return []

    def mod_fail_modified(self, previous_value: Any, new_value: Any) -> None:
        """Modificaiton handler which will always raise an exception."""
        raise AttributeModifyFailure(attribute_name='mod_fail', reason='Built-in test failure')

    @classmethod
    def version(cls) -> ResourceVersion:
        """Fetch the version of the resource provider."""
        return ResourceVersion(major=2, minor=0, build=0, name='FCS')
