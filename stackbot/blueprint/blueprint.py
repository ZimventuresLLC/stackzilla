"""Class for interacting with end-user blueprints."""

from stackbot.blueprint.exceptions import NotLoaded
from stackbot.blueprint.importer import Importer
from stackbot.database.base import StackBotDB
from stackbot.graph import Graph
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

        # Dump all of the modules to the databse
        StackBotDB.db.delete_all_blueprint_modules()
        for module in self.modules.values():
            StackBotDB.db.create_blueprint_module(path=module.path, data=module.data)


    def _build_graph(self) -> Graph:
        """Build a dependency graph from all of the classes that were previously imported."""
        if self.loaded is False:
            raise NotLoaded

        graph = Graph()

        for imported_class in self.classes.values():
            obj = imported_class()
            graph.add_node(imported_class, obj.depends_on())

        return graph
