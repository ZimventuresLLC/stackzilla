"""Module that has all of the logic for diffing imported blueprints."""
from dataclasses import dataclass
from enum import Enum, auto
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

from colorama import Fore, Style

from stackzilla.attribute import StackzillaAttribute
from stackzilla.blueprint.blueprint import StackzillaBlueprint
from stackzilla.database.base import StackzillaDB
from stackzilla.database.exceptions import ResourceNotFound
from stackzilla.diff.exceptions import (ApplyErrors, NoDiffError,
                                        UnhandledAttributeModifications,
                                        VersionIncompatibility)
from stackzilla.graph import Graph
from stackzilla.logger.core import CoreLogger
from stackzilla.resource import AttributeModified, StackzillaResource
from stackzilla.resource.exceptions import (AttributeModifyFailure,
                                            ResourceCreateFailure,
                                            ResourceDeleteFailure)
from stackzilla.utils.constants import DB_BP_PREFIX, DISK_BP_PREFIX
from stackzilla.utils.string import removeprefix


class StackzillaDiffResult(Enum):
    """Enum for the available results from diffing either a resource or parameter."""

    CONFLICT = auto()
    DELETED = auto()
    NEW = auto()
    # This is a superset of CONFLICT, indicating that an attribute difference requies the resource to be destroyed and recreated.
    REBUILD_REQUIRED = auto()
    SAME = auto()


@dataclass
class StackzillaAttributeDiff:
    """Results for the diff operation on a single attribute."""

    src_value: Optional[Any]
    dest_value: Optional[Any]
    src_attribute: Optional[StackzillaAttribute]
    dest_attribute: Optional[StackzillaAttribute]
    result: StackzillaDiffResult

    def filtered_src_value(self) -> Any:
        """Fetch the source value, filtering for secrets or dynamic values."""
        if self.src_attribute.secret:
            return '<secret>'

        if self.src_attribute.dynamic:
            return '<TBD>'

        return str(self.src_value)

    def filtered_dest_value(self) -> Any:
        """Fetch the destination value, filtering for secrets or dynamic values."""
        if self.dest_attribute.secret:
            return '<secret>'

        if self.dest_attribute.dynamic:
            return '<TBD>'

        return str(self.dest_value)

    def is_secret(self) -> bool:
        """Query if the attribute is a secret."""
        if self.src_attribute:
            return self.src_attribute.secret

        if self.dest_attribute:
            return self.dest_attribute.secret

        raise RuntimeError('Unkonwn attribute')

    def name(self) -> str:
        """Fetch the name of the attribute."""
        if self.src_attribute:
            return self.src_attribute.name

        if self.dest_attribute:
            return self.dest_attribute.name

        raise RuntimeError('Unkonwn attribute')


    def print(self, buffer: StringIO) -> None:
        """Print the attribute diff.

        Args:
            buffer (StringIO): Buffer to write to
        """
        if self.result == StackzillaDiffResult.NEW:
            buffer.write(Fore.GREEN + f'++\t{self.name()}: <none> => {self.filtered_src_value()}\n')
        elif self.result == StackzillaDiffResult.DELETED:
            buffer.write(Fore.RED + f'--\t{self.name()}\n')
        elif self.result == StackzillaDiffResult.CONFLICT:
            if self.src_attribute.modify_rebuild:
                buffer.write(Fore.YELLOW + f'!!\t{self.name()}: {self.filtered_dest_value()} => {self.filtered_src_value()}\n')
            else:
                buffer.write(Fore.YELLOW + f'@@\t{self.name()}: {self.filtered_dest_value()} => {self.filtered_src_value()}\n')
        else:
            buffer.write(Fore.WHITE + f'  \t{self.name()}: {self.filtered_dest_value()} => {self.filtered_src_value()}\n')

@dataclass
class StackzillaResourceDiff:
    """Data structure to hold the results of a resource to resource diff."""

    src_resource: Optional[StackzillaResource]
    dest_resource: Optional[StackzillaResource]
    result: StackzillaDiffResult
    attribute_diffs: Dict[str, StackzillaAttributeDiff]

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
        path = removeprefix(string=path, prefix='..')
        path = removeprefix(string=path, prefix=f'{DB_BP_PREFIX}.')
        path = removeprefix(string=path, prefix=f'{DISK_BP_PREFIX}.')

        return path

    def print(self, buffer: StringIO) -> None:
        """Print the diff results to the buffer."""
        if self.result == StackzillaDiffResult.DELETED:
            buffer.write(Fore.RED + f'[{self.path()}] DELETING\n')
        elif self.result == StackzillaDiffResult.NEW:
            buffer.write(Fore.GREEN + f'[{self.path()}] CREATING\n')
        elif self.result == StackzillaDiffResult.REBUILD_REQUIRED:
            buffer.write(Fore.RED + f'[{self.path()}] REBUILD REQUIRED. See attributes marked with "!!"\n')
        elif self.result == StackzillaDiffResult.CONFLICT:
            buffer.write(Fore.YELLOW + f'[{self.path()}] UPDATING\n')
        elif self.result == StackzillaDiffResult.SAME:
            return
        else:
            raise RuntimeError(f'Unhandled state: {self.result}')

        for attribute in self.attribute_diffs.values():
            attribute.print(buffer)

@dataclass
class StackzillaBlueprintDiff:
    """The top-most level of diff."""

    resource_diffs: Dict[str, StackzillaResourceDiff]

    # Valid values are SAME or CONFLICT
    result: StackzillaDiffResult

@dataclass
class StackzillaDiffApplyResult:
    """The results for the application of a single resource."""

    resource_name: str
    result: str
    error: str

class StackzillaDiff:
    """Compute the differences between two collection of modules."""

    def __init__(self) -> None:
        """Default constructor."""
        self._result: StackzillaBlueprintDiff = None
        self._src_blueprint: StackzillaBlueprint = None
        self._dest_blueprint: StackzillaBlueprint = None
        self._logger: CoreLogger = CoreLogger(component='diff')

    @property
    def result(self) -> StackzillaBlueprintDiff:
        """Fetch the result of the previous diff operation."""
        if self._result is None:
            raise NoDiffError

        return self._result

    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    def apply(self):
        """Resolve the blueprint graph and apply differences."""
        # Create a graph from the source blueprint
        graph = Graph()
        for imported_class in self._src_blueprint.resources.values():
            obj = imported_class()
            graph.add_node(imported_class, obj.depends_on())

        # Raises CircularDependency if the graph can not be resolved
        phases = graph.resolve()

        # Implementation Note
        # The blueprint is purposefully being persisted to the database BEFORE it is applied.
        # If a blueprint is partially created/modified, the resource & attribute tables will not
        #  have the data but we need to know what the last blueprint used was.

        # Check the destination blueprint for resources not in the source blueprint (deleted)
        for resource_name in self._dest_blueprint.resources:
            if resource_name not in self._src_blueprint.resources:
                deleted_resource = self._dest_blueprint.resources[resource_name]()
                deleted_resource.delete()
                deleted_resource.delete_from_db()

        # Dump all of the packages to the database
        StackzillaDB.db.delete_all_blueprint_packages()
        for package_name in self._src_blueprint.packages:
            StackzillaDB.db.create_blueprint_package(path=package_name)

        # Dump all of the modules to the databse
        StackzillaDB.db.delete_all_blueprint_modules()
        for module in self._src_blueprint.modules.values():
            StackzillaDB.db.create_blueprint_module(path=module.path, data=module.data)

        errors: List[str] = []
        # pylint: disable=too-many-nested-blocks
        for phase in phases:

            # Get the diffs for each resource in the phase
            for resource in phase:
                obj = resource()

                # Need to load the resource from the database so that any dynamic attributes are present
                # NOTE: If the resource is not in the database, no big deal, we'll just silently fail
                obj.load_from_db(silent_fail=True)

                diff: StackzillaResourceDiff = self._result.resource_diffs[obj.path()]

                if diff.result == StackzillaDiffResult.CONFLICT:

                    # Build a dictionary of AttributeModified objects to track what has and hasn't been handled.
                    modified_attrs = {}
                    for attr_name, attr_diff in diff.attribute_diffs.items():
                        modified_attrs[attr_name] = AttributeModified(name=attr_name,
                                                                      previous_value=attr_diff.dest_value,
                                                                      new_value=attr_diff.src_value,
                                                                      handled=False)

                    # Invoke any StackzillaResource::*_modified() handlers
                    for attr_name, attr_diff in diff.attribute_diffs.items():
                        # _on_attribute_modified() should only be accessed from here.
                        # pylint: disable=protected-access
                        try:
                            if obj._on_attribute_modified(attribute_name=attr_name,
                                                          previous_value=attr_diff.dest_value,
                                                          new_value=attr_diff.src_value):

                                # Note that the attribute modification has been handled
                                modified_attrs[attr_name].handled = True
                        except AttributeModifyFailure as exc:
                            modified_attrs[attr_name].error = exc

                    # Invoke the "all-in-one" handler
                    obj.on_attributes_modified(attributes=modified_attrs)

                    # Check for any unhandled attributes
                    unhandled_attributes = []
                    for attribute in modified_attrs.values():
                        # Just log an error and continue onward. Do NOT persist the value to the database.
                        if attribute.error:
                            errors.append(f'{obj.path(remove_prefix=True)}: {attribute.name} - {attribute.error.reason} ')
                        elif attribute.handled is False:
                            # The attribute wasn't handled - get ready to log a failure!
                            unhandled_attributes.append(attribute)
                        else:
                            # Persist the attribute to the database
                            StackzillaDB.db.update_attribute(resource=obj, name=attribute.name, value=attribute.new_value)

                    if unhandled_attributes:

                        if errors:
                            self._logger.critical('Attribute modify encountered during unhandled attribute exception')
                            self._logger.critical(errors)

                        # Since this is actually a provider failure (usually hit during creation of the provider) it will
                        # raise its own excption and "mask" the modify attribute failures. The developer should fix this
                        # issue first!
                        raise UnhandledAttributeModifications(unhandled_attributes)
                elif diff.result == StackzillaDiffResult.REBUILD_REQUIRED:
                    diff.dest_resource.delete()
                    try:
                        diff.src_resource.create()
                    except ResourceCreateFailure as exc:
                        errors.append(f'{exc.resource_name}: {exc.reason}')
                elif diff.result == StackzillaDiffResult.DELETED:
                    try:
                        diff.dest_resource.delete()
                    except ResourceDeleteFailure as exc:
                        errors.append(f'{exc.resource_name}: {exc.reason}')
                elif diff.result == StackzillaDiffResult.NEW:
                    try:
                        diff.src_resource.create()
                    except ResourceCreateFailure as exc:
                        errors.append(f'{exc.resource_name}: {exc.reason}')
                elif diff.result == StackzillaDiffResult.SAME:
                    continue
                else:
                    raise RuntimeError('Unhandled state')

            # If there were errors in this phase, do not continue
            if errors:
                raise ApplyErrors(errors=errors)




    # pylint: disable=too-many-branches,too-many-locals
    def diff(self, source: Optional[StackzillaBlueprint], destination: Optional[StackzillaBlueprint]):
        """Diff the source (disk) blueprint against the destination (database) blueprint.

        Args:
            source (Optional[StackzillaBlueprint]): The on-disk blueprint
            destination (Optional[StackzillaBlueprint]): The in-database blueprint

        Returns:
            StackzillaBlueprintDiff: The results of the diff operation
        """
        self._src_blueprint = source
        self._dest_blueprint = destination

        result = StackzillaDiffResult.SAME
        diffs: Dict[str, StackzillaResourceDiff] = {}

        src_resources: Dict[str, StackzillaResource] = source.resources
        dest_resources: Dict[str, StackzillaResource] = destination.resources

        # The keys for the src_resource are prefixed with the 'sz_disk_bp' prefix.
        src_resource_names_original = list(src_resources)
        for resource_name in src_resource_names_original:
            new_key_name = resource_name.replace(DISK_BP_PREFIX, '.')
            src_resources[new_key_name] = src_resources[resource_name]
            del src_resources[resource_name]

        # The keys for dest_resource are prefixed with the 'sz_db_bp' prefix. Replace it with '.' to match
        # the blueprint paths in a non-namespaced blueprint.
        # ex: sb_db_bp.servers.webserver.MyWebserverVolume => ..servers.webserver.MyWebserverVolume
        dest_resource_names_original = list(dest_resources)
        for resource_name in dest_resource_names_original:
            new_key_name = resource_name.replace(DB_BP_PREFIX, '.')
            dest_resources[new_key_name] = dest_resources[resource_name]
            del dest_resources[resource_name]

        # If the blueprint contains resources not in the database, omit them from consideration
        for resource_name in list(dest_resources.keys()):
            dest_resource: StackzillaResource = dest_resources[resource_name]()

            try:
                dest_resource.load_from_db()
            except ResourceNotFound:
                del dest_resources[resource_name]

        # Pass 1 - diff the source against the destination
        for resource_name in src_resources:

            # NOTE: We are instantiating the resource object and using that instead of the class object
            src_resource: StackzillaResource = src_resources[resource_name]()

            # Is the resource available in both the source and destination
            if resource_name in dest_resources:
                dest_resource: StackzillaResource = dest_resources[resource_name]()
                dest_resource.load_from_db()

                # Check for version incompatibilities
                self.compare_versions(source=src_resource, destination=dest_resource)

                # Diff the resource versions
                attr_diff_result, attr_diffs = self.compare_attributes(source=src_resource, destination=dest_resource)

                if attr_diff_result == StackzillaDiffResult.SAME:
                    # Nothing to do - move along!
                    diffs[resource_name] = StackzillaResourceDiff(src_resource=src_resource,
                                                                  dest_resource=dest_resource,
                                                                  result=StackzillaDiffResult.SAME,
                                                                  attribute_diffs={})
                    continue

                if attr_diff_result in [StackzillaDiffResult.CONFLICT, StackzillaDiffResult.REBUILD_REQUIRED]:
                    result = attr_diff_result
                    diffs[resource_name] = StackzillaResourceDiff(src_resource=src_resource,
                                                                  dest_resource=dest_resource,
                                                                  result=result,
                                                                  attribute_diffs=attr_diffs)

                else:
                    raise RuntimeError('Invalid diff result detected')

            else:
                result = StackzillaDiffResult.CONFLICT

                # All of the attributes are new, create "diff" objects for them.
                new_attr_diffs = {}
                src_attributes = src_resource.attributes
                for attr_name in src_attributes:
                    new_attr_diffs[attr_name] = StackzillaAttributeDiff(src_attribute=src_attributes[attr_name],
                                                                      dest_attribute=None,
                                                                      result=StackzillaDiffResult.NEW,
                                                                      src_value=src_resource.get_attribute_value(attr_name),
                                                                      dest_value=None)

                # This is a new resource
                diffs[resource_name] = StackzillaResourceDiff(src_resource=src_resource,
                                                            dest_resource=None,
                                                            result=StackzillaDiffResult.NEW,
                                                            attribute_diffs=new_attr_diffs)

        # Pass 2 - diff the destination against the source, looking for resources that have been deleted
        for resource_name in dest_resources:
            # NOTE: We are using an object instance here
            dest_resource: StackzillaResource = dest_resources[resource_name]()

            # No need to diff this again
            if resource_name in diffs:
                continue

            result = StackzillaDiffResult.CONFLICT

            # All of the attributes are new, create "diff" objects for them.
            old_attr_diffs = {}
            dest_attributes = dest_resource.attributes
            for attr_name in dest_attributes:
                old_attr_diffs[attr_name] = StackzillaAttributeDiff(src_attribute=None,
                                                                  dest_attribute=dest_attributes[attr_name],
                                                                  result=StackzillaDiffResult.DELETED,
                                                                  src_value=None,
                                                                  dest_value=dest_resource.get_attribute_value(attr_name))

            # The resource has been deleted
            diffs[resource_name] = StackzillaResourceDiff(src_resource=None,
                                                        dest_resource=dest_resource,
                                                        result=StackzillaDiffResult.DELETED,
                                                        attribute_diffs=old_attr_diffs)

        self._result = StackzillaBlueprintDiff(resource_diffs=diffs, result=result)

    def compare_attributes(self,
                source: StackzillaResource,
                destination: StackzillaResource) -> Tuple[StackzillaDiffResult, Dict[str, StackzillaAttributeDiff]]:
        """Compare two resources and returns the attribute differences between them.

        Args:
            source (StackzillaResource): The source resource
            destination (StackzillaResource): The destination resource

        Returns:
            Tuple[StackBodiff_resulttDiffResult, List[StackzillaAttributeDiff]]:
                The top level diff result for the resources, and a list of attribute differences between the resources.
        """
        result = StackzillaDiffResult.SAME

        results: Dict[str, StackzillaAttributeDiff] = {}

        src_attributes: Dict[str, StackzillaAttribute] = source.attributes
        dest_attributes: Dict[str, StackzillaAttribute] = destination.attributes

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
                        result = StackzillaDiffResult.REBUILD_REQUIRED
                    elif src_attributes[attr_name].dynamic:
                        continue
                    else:
                        # Mark the resource-to-resource diff as CONFLICT, assuming the current diff result is not REBUILD.
                        if result != StackzillaDiffResult.REBUILD_REQUIRED:
                            result = StackzillaDiffResult.CONFLICT

                    results[attr_name] = StackzillaAttributeDiff(src_attribute=src_attributes[attr_name],
                                                                 dest_attribute=dest_attributes[attr_name],
                                                                 result=StackzillaDiffResult.CONFLICT,
                                                                 src_value=src_val,
                                                                 dest_value=dest_val)

            else:
                # Mark the resource-to-resource diff as CONFLICT, assuming the current diff result is not REBUILD.
                if result != StackzillaDiffResult.REBUILD_REQUIRED:
                    result = StackzillaDiffResult.CONFLICT

                # This is a new attribute
                results[attr_name] = StackzillaAttributeDiff(src_attribute=src_attributes[attr_name],
                                                           dest_attribute=None,
                                                           result=StackzillaDiffResult.NEW,
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
                        result = StackzillaDiffResult.REBUILD_REQUIRED
                    elif dest_attributes[attr_name].dynamic:
                        continue
                    else:
                        # Mark the resource-to-resource diff as CONFLICT, assuming the current diff result is not REBUILD.
                        if result != StackzillaDiffResult.REBUILD_REQUIRED:
                            result = StackzillaDiffResult.CONFLICT

                    results[attr_name] = StackzillaAttributeDiff(src_attribute=src_attributes[attr_name],
                                                               dest_attribute=dest_attributes[attr_name],
                                                               result=StackzillaDiffResult.CONFLICT,
                                                               src_value=src_val,
                                                               dest_value=dest_val)
            else:
                # Mark the resource-to-resource diff as CONFLICT, assuming the current diff result is not REBUILD.
                if result != StackzillaDiffResult.REBUILD_REQUIRED:
                    result = StackzillaDiffResult.CONFLICT

                # The attribute was deleted from the source
                results[attr_name] = StackzillaAttributeDiff(src_attribute=None,
                                                           dest_attribute=dest_attributes[attr_name],
                                                           result=StackzillaDiffResult.DELETED,
                                                           src_value=None,
                                                           dest_value=dest_val)

        return (result, results)

    def compare_versions(self, source: StackzillaResource, destination: StackzillaResource):
        """Compare the resources, checking for incompatible major version numbers.

        Args:
            source (StackzillaResource): The new resource (disk version)
            destination (StackzillaResource): The original resource (database version)

        Raises:
            VersionIncompatibility: Raised when there is a mismatch
        """
        if source.version().major != destination.saved_version().major:
            raise VersionIncompatibility(
                f'{source.path(True)} provider version mismatch: {source.version().major} != {destination.saved_version().major}'
            )


    def print(self, buffer: StringIO) -> None:
        """Print the results of a diff.

        Args:
            diff (StackzillaBlueprintDiff): The previously created diff.
            buffer (StringIO): The buffer used for printing.
        """
        if self._result is None:
            raise NoDiffError

        for resource in self._result.resource_diffs.values():
            resource.print(buffer)

        # Reset the color style
        buffer.write(Style.RESET_ALL)
