"""Class for interacting with end-user blueprints."""
from typing import Optional, Type

from stackbot.importer.exceptions import NotLoaded
from stackbot.importer.importer import Importer
from stackbot.importer.db_importer import DatabaseImporter
from stackbot.database.base import StackBotDB
from stackbot.graph import Graph
from stackbot.resource.base import StackBotResource


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
                class_filter=StackBotBlueprint.base_resource_type, package_root='sb_db_bp'
            )

    def load(self):
        """Load the blueprint into the Python namespace."""
        self._importer.load()

    @property
    def resources(self) -> dict[str, StackBotResource]:
        """Fetch all of the resources available in the blueprint

        Returns:
            dict[str, StackBotResource]: A dictionary of resources. The key is the full Python path to the resource.
        """
        return self._importer.classes

    def verify(self):
        """Verify all of the blueprint resources."""

        graph = self._build_graph()
        # Will raise CircularDependency if the graph can not be resolved
        graph.resolve()

        # TODO: Verify all of the attributes

    def apply(self):
        """Execute the dependency graph for the blueprint."""

        graph: Graph = self._build_graph()
        phases = graph.resolve()

        for phase in phases:

            # TODO: Make this multi-threaded since none of the resources within a phase will depend on each other
            for resource in phase:

                obj = resource()

                # TODO: Handle the update/delete case
                obj.create()
                obj.create_in_db()

        # Dump all of the packages to the database
        StackBotDB.db.delete_all_blueprint_packages()
        for package_name in self._importer.packages:
            StackBotDB.db.create_blueprint_package(path=package_name)

        # Dump all of the modules to the databse
        StackBotDB.db.delete_all_blueprint_modules()
        for module in self._importer.modules.values():
            StackBotDB.db.create_blueprint_module(path=module.path, data=module.data)


    def _build_graph(self) -> Graph:
        """Build a dependency graph from all of the classes that were previously imported."""
        if self._importer.loaded is False:
            raise NotLoaded

        graph = Graph()

        for imported_class in self._importer.classes.values():
            obj = imported_class()
            graph.add_node(imported_class, obj.depends_on())

        return graph
