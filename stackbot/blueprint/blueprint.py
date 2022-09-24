"""Class for interacting with end-user blueprints."""

from stackbot.blueprint.importer import Importer
from stackbot.resource.base import StackBotResource


class Blueprint(Importer):
    """Manage an end-user blueprint."""

    base_resource_type = StackBotResource

    def __init__(self, path: str):
        """Blueprint constructor.

        Args:
            path (str): Filesystem path to the top-level blueprint directory
        """
        super().__init__(path, class_filter=Blueprint.base_resource_type)


    def verify(self):
        """Verify all of the blueprint resources."""

    def apply(self):
        """Execute the dependency graph for the blueprint."""
