"""Test resource provider that mimics an application load balancer."""
from typing import List

from stackzilla.attribute.attribute import StackzillaAttribute
from stackzilla.provider.null.base import BaseNullResource


class LoadBalancer(BaseNullResource):
    """Dummy instance resource."""

    type = StackzillaAttribute(required=True, choices=['network', 'application'])
    instances = StackzillaAttribute()

    def __init__(self) -> None:
        """Default constructor that sets up logging."""
        super().__init__(provider_name='stackzilla.provider.null.instance')

    def depends_on(self) -> List['StackzillaResource']:
        """Add any instances to the dependency graph."""
        dependencies = super().depends_on()

        for instance in self.instances:
            dependencies.append(instance)

        return dependencies
