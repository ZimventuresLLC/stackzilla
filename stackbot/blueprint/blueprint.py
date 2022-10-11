"""Class for interacting with end-user blueprints."""
from typing import Optional

from stackbot.importer.exceptions import NotLoaded
from stackbot.importer.base import ModuleInfo
from stackbot.importer.importer import Importer
from stackbot.importer.db_importer import DatabaseImporter
from stackbot.graph import Graph
from stackbot.resource.base import StackBotResource
from stackbot.utils.constants import DB_BP_PREFIX

class StackBotBlueprint:
    """Manage an end-user blueprint."""

    base_resource_type = StackBotResource

    def __init__(self, path: Optional[str] = None):
        """Blueprint constructor.

        Args:
            path (str): Filesystem path to the top-level blueprint directory.
                        If None, the blueprint will be loaded from the database.
        """
        super().__init__()

        if path:
            self._importer = Importer(path=path, class_filter=StackBotBlueprint.base_resource_type)
        else:
            self._importer = DatabaseImporter(
                class_filter=StackBotBlueprint.base_resource_type, package_root=DB_BP_PREFIX
            )

    def load(self):
        """Load the blueprint into the Python namespace."""
        self._importer.load()

    @property
    def resources(self) -> dict[str, StackBotResource]:
        """Fetch all of the resources available in the blueprint.

        Returns:
            dict[str, StackBotResource]: A dictionary of resources. The key is the full Python path to the resource.
        """
        return self._importer.classes

    @property
    def packages(self) -> dict[str, ModuleInfo]:
        """Fetch a mapping of all of the packages available in the blueprint.

        Returns:
            dict[str, ModuleInfo]: A dictionary of ModuleInfo, key'ed by the Python path
        """
        return self._importer.packages

    @property
    def modules(self) -> dict[str, ModuleInfo]:
        """A mapping of all the modules available in the blueprint.

        Returns:
            dict[str, ModuleInfo]: ModuleInfo for each module, key'ed by the Python path
        """
        return self._importer.modules

    def verify(self):
        """Verify all of the blueprint resources."""

        graph = self._build_graph()
        # Will raise CircularDependency if the graph can not be resolved
        graph.resolve()

        # TODO: Verify all of the attributes

    def _build_graph(self) -> Graph:
        """Build a dependency graph from all of the classes that were previously imported."""
        if self._importer.loaded is False:
            raise NotLoaded

        graph = Graph()

        for imported_class in self._importer.classes.values():
            obj = imported_class()
            graph.add_node(imported_class, obj.depends_on())

        return graph
