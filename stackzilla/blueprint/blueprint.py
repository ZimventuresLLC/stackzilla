"""Class for interacting with end-user blueprints."""
from typing import List, Optional

from stackzilla.blueprint.exceptions import BlueprintVerifyFailure
from stackzilla.graph import Graph
from stackzilla.importer.base import ModuleInfo
from stackzilla.importer.db_importer import DatabaseImporter
from stackzilla.importer.exceptions import NotLoaded
from stackzilla.importer.importer import Importer
from stackzilla.resource.base import StackzillaResource
from stackzilla.resource.exceptions import ResourceVerifyError
from stackzilla.utils.constants import DB_BP_PREFIX


class StackzillaBlueprint:
    """Manage an end-user blueprint."""

    base_resource_type = StackzillaResource

    def __init__(self, path: Optional[str] = None):
        """Blueprint constructor.

        Args:
            path (str): Filesystem path to the top-level blueprint directory.
                        If None, the blueprint will be loaded from the database.
        """
        super().__init__()

        if path:
            self._importer = Importer(path=path, class_filter=StackzillaBlueprint.base_resource_type)
        else:
            self._importer = DatabaseImporter(
                class_filter=StackzillaBlueprint.base_resource_type, package_root=DB_BP_PREFIX
            )

    def load(self):
        """Load the blueprint into the Python namespace."""
        self._importer.load()

    @property
    def resources(self) -> dict[str, StackzillaResource]:
        """Fetch all of the resources available in the blueprint.

        Returns:
            dict[str, StackzillaResource]: A dictionary of resources. The key is the full Python path to the resource.
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
        """Invoke the verify method for each resource in the blueprint.

        Raises:
            BlueprintVerifyFailure: Raised if any of the resources raise a verification error
        """
        # Will raise CircularDependency if the graph can not be resolved
        graph = self.build_graph()
        graph.resolve()

        # Verify all of the resources
        resource_verify_errors: List[ResourceVerifyError] = []
        for resource in self.resources.values():
            obj = resource()
            try:
                obj.verify()
            except ResourceVerifyError as verify_err:
                resource_verify_errors.append(verify_err)

        # Assemble the individual resource verify errors into a single exception
        if resource_verify_errors:
            raise BlueprintVerifyFailure(errors=resource_verify_errors)

    def build_graph(self) -> Graph:
        """Build a dependency graph from all of the classes that were previously imported."""
        if self._importer.loaded is False:
            raise NotLoaded

        graph = Graph()

        for imported_class in self._importer.classes.values():
            obj = imported_class()
            graph.add_node(imported_class, obj.depends_on())

        return graph
