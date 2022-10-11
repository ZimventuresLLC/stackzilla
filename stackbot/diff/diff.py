"""Module that has all of the logic for diffing imported blueprints."""
from colorama import Fore, Style
from dataclasses import dataclass
from enum import Enum, auto
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

from stackbot.blueprint.blueprint import StackBotBlueprint
from stackbot.database.base import StackBotDB
from stackbot.diff.exceptions import NoDiffError
from stackbot.graph import Graph
from stackbot.resource import StackBotResource
from stackbot.attribute import StackBotAttribute
from stackbot.utils.constants import DB_BP_PREFIX

class StackBotDiffResult(Enum):
    """Enum for the available results from diffing either a resource or parameter."""
    CONFLICT = auto()
    DELETED = auto()
    NEW = auto()
    REBUILD_REQUIRED = auto()   # This is a superset of CONFLICT, indicating that an attribute difference requies the resource to be destroyed and recreated.
    SAME = auto()


@dataclass
class StackBotAttributeDiff:
    """Results for the diff operation on a single attribute."""
    src_value: Optional[Any]
    dest_value: Optional[Any]
    src_attribute: Optional[StackBotAttribute]
    dest_attribute: Optional[StackBotAttribute]
    result: StackBotDiffResult

    def filtered_src_value(self) -> Any:
        """Fetch the source value, filtering for secrets or dynamic values."""
        if self.src_attribute.secret:
            return '<secret>'
        elif self.src_attribute.dynamic:
            return '<TBD>'
        else:
            return self.src_value

    def filtered_dest_value(self) -> Any:
        """Fetch the destination value, filtering for secrets or dynamic values."""
        if self.dest_attribute.secret:
            return '<secret>'
        elif self.dest_attribute.dynamic:
            return '<TBD>'
        else:
            return self.dest_value

    def is_secret(self) -> bool:
        """Query if the attribute is a secret."""
        if self.src_attribute:
            return self.src_attribute.secret
        elif self.dest_attribute:
            return self.dest_attribute.secret
        else:
            raise RuntimeError('Unkonwn attribute')

    def name(self) -> str:
        """Fetch the name of the attribute"""
        if self.src_attribute:
            return self.src_attribute.name
        elif self.dest_attribute:
            return self.dest_attribute.name
        else:
            raise RuntimeError('Unkonwn attribute')


    def print(self, buffer: StringIO) -> None:
        """Print the attribute diff.

        Args:
            buffer (StringIO): Buffer to write to
        """
        if self.result == StackBotDiffResult.NEW:
            buffer.write(Fore.GREEN + f'++\t{self.name()}: <none> => {self.filtered_src_value()}\n')
        elif self.result == StackBotDiffResult.DELETED:
            buffer.write(Fore.RED + f'--\t{self.name()}\n')
        elif self.result == StackBotDiffResult.CONFLICT:
            if self.src_attribute.modify_rebuild:
                buffer.write(Fore.YELLOW + f'!!\t{self.name()}: {self.dest_value} => {self.src_value}\n')
            else:
                buffer.write(Fore.YELLOW + f'@@\t{self.name()}: {self.dest_value} => {self.src_value}\n')
        else:
            buffer.write(Fore.WHITE + f'  \t{self.name()}: {self.dest_value} => {self.src_value}\n')

@dataclass
class StackBotResourceDiff:
    """Data structure to hold the results of a resource to resource diff."""
    src_resource: Optional[StackBotResource]
    dest_resource: Optional[StackBotResource]
    result: StackBotDiffResult
    attribute_diffs: List[StackBotAttributeDiff]

    def path(self) -> str:
        """Fetch the Python path for the resource."""
        path: str = ''
        if self.src_resource:
            path = self.src_resource.path()
        elif self.dest_resource:
            path = self.dest_resource.path()
        else:
            raise RuntimeError('Unknown Resource')

        # ALWAYS Remove the leading '..' or DB prefix
        path = path.removeprefix('..')
        path = path.removeprefix(f'{DB_BP_PREFIX}.')

        return path
        
    def print(self, buffer: StringIO) -> None:
        """Print the diff results to the buffer."""
        if self.result == StackBotDiffResult.DELETED:
            buffer.write(Fore.RED + f'DELETING [{self.path()}]\n')
        elif self.result == StackBotDiffResult.NEW:
            buffer.write(Fore.GREEN + f'CREATING [{self.path()}]\n')
        elif self.result == StackBotDiffResult.REBUILD_REQUIRED:
            buffer.write(Fore.YELLOW + 'REBUILD REQUIRED. See attributes marked with "!!"\n')

        for attribute in self.attribute_diffs:
            attribute.print(buffer)

@dataclass
class StackBotBlueprintDiff:
    """The top-most level of diff."""
    resource_diffs: Dict[str, StackBotResourceDiff]

    # Valid values are SAME or CONFLICT
    result: StackBotDiffResult

class StackBotDiff:
    """Compute the differences between two collection of modules."""

    def __init__(self) -> None:
        self._result: StackBotBlueprintDiff = None
        self._src_blueprint: StackBotBlueprint = None
        self._dest_blueprint: StackBotBlueprint = None

    @property
    def result(self) -> StackBotBlueprintDiff:
        """Fetch the result of the previous diff operation."""
        if self._result is None:
            raise NoDiffError

        return self._result

    def apply(self):

        # Create a graph from the source blueprint
        graph = Graph()
        for imported_class in self._src_blueprint.resources.values():
            obj = imported_class()
            graph.add_node(imported_class, obj.depends_on())

        # Raises CircularDependency if the graph can not be resolved
        phases = graph.resolve()

        for phase in phases:

            # TODO: Make this multi-threaded since none of the resources within a phase will depend on each other
            # Get the diffs for each resource in the phase
            for resource in phase:
                diff: StackBotResourceDiff = self._result.resource_diffs[resource.path()]

                if diff.result == StackBotDiffResult.CONFLICT:
                    diff.src_resource.update()
                elif diff.result == StackBotDiffResult.DELETED:
                    diff.dest_resource.delete()
                    diff.dest_resource.delete_from_db()
                elif diff.result == StackBotDiffResult.NEW:
                    diff.src_resource.create()
                    diff.src_resource.create_in_db()
                elif diff.result == StackBotDiffResult.SAME:
                    continue
                else:
                    raise RuntimeError('Unhandled state')

        # Check the destination blueprint for resources not in the source blueprint (deleted)
        for resource_name in self._dest_blueprint.resources:
            if resource_name not in self._src_blueprint.resources:
                deleted_resource = self._dest_blueprint.resources[resource_name]()
                deleted_resource.delete()
                deleted_resource.delete_from_db()

        # Dump all of the packages to the database
        StackBotDB.db.delete_all_blueprint_packages()
        for package_name in self._src_blueprint.packages:
            StackBotDB.db.create_blueprint_package(path=package_name)

        # Dump all of the modules to the databse
        StackBotDB.db.delete_all_blueprint_modules()
        for module in self._src_blueprint.modules.values():
            StackBotDB.db.create_blueprint_module(path=module.path, data=module.data)

    def diff(self, source: Optional[StackBotBlueprint], destination: Optional[StackBotBlueprint]):
        """Diff the source (disk) blueprint against the destination (database) blueprint.

        Args:
            source (Optional[StackBotBlueprint]): The on-disk blueprint
            destination (Optional[StackBotBlueprint]): The in-database blueprint

        Returns:
            StackBotBlueprintDiff: The results of the diff operation
        """
        self._src_blueprint = source
        self._dest_blueprint = destination

        result = StackBotDiffResult.SAME
        diffs: Dict[str, StackBotResourceDiff] = {}

        src_resources: Dict[str, StackBotResource] = source.resources
        dest_resources: Dict[str, StackBotResource] = destination.resources

        # The keys for dest_resource are prefixed with the 'sb_db_bp' prefix. Replace it with '.' to match 
        # the blueprint paths in a non-namespaced blueprint.
        # ex: sb_db_bp.servers.webserver.MyWebserverVolume => ..servers.webserver.MyWebserverVolume        
        dest_resource_names_original = list(dest_resources)
        for resource_name in dest_resource_names_original:
            new_key_name = resource_name.replace(DB_BP_PREFIX, '.')
            dest_resources[new_key_name] = dest_resources[resource_name]
            del dest_resources[resource_name]

        # Pass 1 - diff the source against the destination
        for resource_name in src_resources:
            
            # NOTE: We are instantiating the resource object and using that instead of the class object
            src_resource: StackBotResource = src_resources[resource_name]()

            # Is the resource available in both the source and destination
            if resource_name in dest_resources:
                dest_resource: StackBotResource = dest_resources[resource_name]()

                # Diff the resources
                attr_diff_result, attr_diffs = self.compare(source=src_resource, destination=dest_resource)

                if attr_diff_result == StackBotDiffResult.SAME:
                    # Nothing to do - move along!
                    diffs[resource_name] = StackBotResourceDiff(src_resource=src_resource,
                                                                dest_resource=dest_resource,
                                                                result=StackBotDiffResult.SAME,
                                                                attribute_diffs=[])
                    continue

                elif attr_diff_result == StackBotDiffResult.CONFLICT or attr_diff_result == StackBotDiffResult.REBUILD_REQUIRED:
                    result = StackBotDiffResult.CONFLICT
                    diffs[resource_name] = StackBotResourceDiff(src_resource=src_resource,
                                                                dest_resource=dest_resource,
                                                                result=result,
                                                                attribute_diffs=attr_diffs)

                else:
                    raise RuntimeError('Invalid diff result detected')

            else:
                result = StackBotDiffResult.CONFLICT

                # All of the attributes are new, create "diff" objects for them.
                new_attr_diffs = []
                src_attributes = src_resource.attributes
                for attr_name in src_attributes:
                    new_attr_diffs.append(StackBotAttributeDiff(src_attribute=src_attributes[attr_name],
                                                                dest_attribute=None,
                                                                result=StackBotDiffResult.NEW,
                                                                src_value=src_resource.get_attribute_value(attr_name),
                                                                dest_value=None))

                # This is a new resource
                diffs[resource_name] = StackBotResourceDiff(src_resource=src_resource,
                                                            dest_resource=None,
                                                            result=StackBotDiffResult.NEW,
                                                            attribute_diffs=new_attr_diffs)

        # Pass 2 - diff the destination against the source, looking for resources that have been deleted
        for resource_name in dest_resources:
            # NOTE: We are using an object instance here
            dest_resource: StackBotResource = dest_resources[resource_name]()

            # No need to diff this again
            if resource_name in diffs:
                continue
            else:
                result = StackBotDiffResult.CONFLICT

                # All of the attributes are new, create "diff" objects for them.
                old_attr_diffs = []
                dest_attributes = dest_resource.attributes
                for attr_name in dest_attributes:
                    old_attr_diffs.append(StackBotAttributeDiff(src_attribute=None,
                                                                dest_attribute=dest_attributes[attr_name],
                                                                result=StackBotDiffResult.DELETED,
                                                                src_value=None,
                                                                dest_value=dest_resource.get_attribute_value(attr_name)))

                # The resource has been deleted
                diffs[resource_name] = StackBotResourceDiff(src_resource=None,
                                                            dest_resource=dest_resource,
                                                            result=StackBotDiffResult.DELETED,
                                                            attribute_diffs=old_attr_diffs)

        self._result = StackBotBlueprintDiff(resource_diffs=diffs, result=result)

    def compare(self, source: StackBotResource, destination: StackBotResource) -> Tuple[StackBotDiffResult, List[StackBotAttributeDiff]]:
        """Compare two resources and returns the attribute differences between them.

        Args:
            source (StackBotResource): The source resource
            destination (StackBotResource): The destination resource

        Returns:
            Tuple[StackBodiff_resulttDiffResult, List[StackBotAttributeDiff]]: The top level diff result for the resources, and a list of attribute differences between the resources.
        """

        # TODO: Ensure the resource versions are compatible
        result = StackBotDiffResult.SAME

        results: Dict[str, StackBotAttributeDiff] = {}

        src_attributes: Dict[str, StackBotAttribute] = source.attributes
        dest_attributes: Dict[str, StackBotAttribute] = destination.attributes

        # Check if the attribute is in the source, but not the dest
        for attr_name in src_attributes:

            src_val = source.get_attribute_value(attr_name)

            if attr_name in dest_attributes:

                # Diff the attributes here
                dest_val = destination.get_attribute_value(attr_name)

                # The attribute values do not match!
                if src_val != dest_val:

                    # Mark the entire resource-to-resource diff as needing a rebuild
                    if src_attributes[attr_name].modify_rebuild:
                        result = StackBotDiffResult.REBUILD_REQUIRED
                    else:
                        # Mark the resource-to-resource diff as CONFLICT, assuming the current diff result is not REBUILD.
                        if result != StackBotDiffResult.REBUILD_REQUIRED:
                            result = StackBotDiffResult.CONFLICT

                    results[attr_name] = StackBotAttributeDiff(src_attribute=src_attributes[attr_name],
                                                               dest_attribute=dest_attributes[attr_name],
                                                               result=StackBotDiffResult.CONFLICT,
                                                               src_value=src_val,
                                                               dest_value=dest_val)

            else:
                # Mark the resource-to-resource diff as CONFLICT, assuming the current diff result is not REBUILD.
                if result != StackBotDiffResult.REBUILD_REQUIRED:
                    result = StackBotDiffResult.CONFLICT

                # This is a new attribute
                results[attr_name] = StackBotAttributeDiff(src_attribute=src_attributes[attr_name],
                                                           dest_attribute=None,
                                                           result=StackBotDiffResult.NEW,
                                                           src_value=src_val,
                                                           dest_value=None)

        # Check if the attribute is in the dest, but not the source
        for attr_name in dest_attributes:

            dest_val = destination.get_attribute_value(attr_name)

            if attr_name in src_attributes:
                # Only perform the diff if this attribute wasn't handled in the src_attributes loop above
                if attr_name in results:
                    continue

                # Diff the attributes here
                src_val = source.get_attribute_value(attr_name)

                if src_val != dest_val:

                    # Mark the entire resource-to-resource diff as needing a rebuild
                    if dest_attributes[attr_name].modify_rebuild:
                        result = StackBotDiffResult.REBUILD_REQUIRED
                    else:
                        # Mark the resource-to-resource diff as CONFLICT, assuming the current diff result is not REBUILD.
                        if result != StackBotDiffResult.REBUILD_REQUIRED:
                            result = StackBotDiffResult.CONFLICT

                    results[attr_name] = StackBotAttributeDiff(src_attribute=src_attributes[attr_name],
                                                               dest_attribute=dest_attributes[attr_name],
                                                               result=StackBotDiffResult.CONFLICT,
                                                               src_value=src_val,
                                                               dest_value=dest_val)
            else:
                # Mark the resource-to-resource diff as CONFLICT, assuming the current diff result is not REBUILD.
                if result != StackBotDiffResult.REBUILD_REQUIRED:
                    result = StackBotDiffResult.CONFLICT

                # The attribute was deleted from the source
                results[attr_name] = StackBotAttributeDiff(src_attribute=None,
                                                           dest_attribute=dest_attributes[attr_name],
                                                           result=StackBotDiffResult.DELETED,
                                                           src_value=None,
                                                           dest_value=dest_val)

        return (result, results)

    def print(self, buffer: StringIO) -> None:
        """Print the results of a diff.

        Args:
            diff (StackBotBlueprintDiff): The previously created diff.
            buffer (StringIO): The buffer used for printing.
        """
        if self._result is None:
            raise NoDiffError

        for resource in self._result.resource_diffs.values():
            resource.print(buffer)

        # Reset the color style
        buffer.write(Style.RESET_ALL)
