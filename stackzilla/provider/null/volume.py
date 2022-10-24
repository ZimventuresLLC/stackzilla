"""Test resource provider that mimics a storage volume."""
from typing import List

from stackzilla.attribute.attribute import StackzillaAttribute
from stackzilla.provider.null.base import BaseNullResource
from stackzilla.resource.base import StackzillaResource

from .instance import Instance


class Volume(BaseNullResource):
    """Dummy volume resource."""

    format = StackzillaAttribute(required=False, choices=['xfs', 'hdfs', 'fat'], default='xfs')
    size = StackzillaAttribute(required=True)
    instance = StackzillaAttribute(required=False, types=[Instance])

    create_failure = False

    def __init__(self) -> None:
        """Default constructor that sets up logging."""
        super().__init__(provider_name='stackzilla.provider.null.volume')

    def depends_on(self) -> List['StackzillaResource']:
        """Required to be overridden."""
        dependencies = super().depends_on()

        if self.instance:
            dependencies.append(self.instance)

        return dependencies
