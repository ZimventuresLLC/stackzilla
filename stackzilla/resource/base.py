"""Base class for all user defined resources."""
import inspect
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from stackzilla.attribute import StackzillaAttribute
from stackzilla.database.base import StackzillaDB
from stackzilla.database.exceptions import AttributeNotFound, ResourceNotFound
from stackzilla.logger.core import CoreLogger
from stackzilla.resource.exceptions import (AttributeModifyFailure,
                                            ResourceVerifyError)
from stackzilla.utils.constants import DB_BP_PREFIX, DISK_BP_PREFIX
from stackzilla.utils.string import removeprefix


@dataclass
class AttributeModified:
    """Data structure to store attribute modification data."""

    name: str
    previous_value: Any
    new_value: Any
    handled: bool = False
    error: Optional[AttributeModifyFailure] = None


@dataclass
class ResourceVersion:
    """Data structure to represent versioning information for a StackzillaResource."""

    major: int
    minor: int
    build: int
    name: str

######################################################################################
# The SZMeta class provides an equality operator for when StackzillaResource classes
# are compared (obj == obj2). Normally, Python would simply use the object's id.
# For our case, we want to use the normalized Python path (remove the prefix).
# In addition, the __repr__ class will allow any object to have str() applied to it
# and the normalized Python path will be returned.
######################################################################################
class SZMeta(type):
    """Metaclass which provides custom operators for the StackzillaResource class."""

    def __repr__(cls) -> str:
        """Return the normalized path as the string represntation of the class."""
        return cls.path()

    def __eq__(cls, other: 'StackzillaResource') -> bool:
        """Perform an equality check using the path of the resource."""
        try:
            return cls.path() == other.path()
        except AttributeError:
            # Raised when .path() doesn't exist -> which it won't for obects that aren't StackzillaResource types.
            return False

    def __hash__(cls) -> int:
        """Must be overridden any time __eq__ is overridden."""
        return id(cls)


class StackzillaResource(metaclass=SZMeta):
    """Base class for all user defined resources."""

    def __init__(self) -> None:
        """Base constructor for all Stackzilla resource types."""
        self._core_logger = CoreLogger(component='resource')

        # The provider version at the time of persistance into the database.
        # This is used during the blueprint diff/verification process
        self._saved_version: Optional[ResourceVersion] = None

    @classmethod
    def path(cls, remove_prefix: bool=False) -> str:
        """A unique name (within the blueprint) for this resource."""
        path = f'{cls.__module__}.{cls.__name__}'

        # Always replace the DB prevfix
        if path.startswith(DB_BP_PREFIX):
            path = path.replace(DB_BP_PREFIX, '.')

        if path.startswith(DISK_BP_PREFIX):
            path = path.replace(DISK_BP_PREFIX, '.')

        # Optionally remove the '..' prefix
        if remove_prefix:
            path = removeprefix(string=path, prefix='..')

        return path

    def create(self) -> None:
        """Create a new resource."""
        self.create_in_db()

    def update(self) -> None:
        """Apply the changes to this resource."""
        # Update any resource details
        StackzillaDB.db.update_resource(resource=self)

        for name in self.attributes:
            StackzillaDB.db.update_attribute(resource=self, name=name, value=getattr(self, name))

    def delete(self) -> None:
        """Delete a previously created resource."""
        self.delete_from_db()

    @abstractmethod
    def depends_on(self) -> List['StackzillaResource']:
        """Return a list of other resources that must be applied before this resource can be applied.

        Returns:
            List[StackzillaResource]: List of StackzillaResource classes that must be applied prior to this resource.
        """
        return []

    # pylint: disable=too-many-branches
    def verify(self) -> None:
        """Verify all of the attributes within the resource.

        Raises:
            ResourceVerifyError: Raised if any of the attribute verifications fail.
        """
        # The exception that will be raised, if any issues are found
        verify_error_info = ResourceVerifyError(resource_name=self.path(True))

        for attr_name, attribute in self.attributes.items():

            # Get the attribute value from the resource
            attr_value = self.get_attribute_value(name=attr_name)

            # Verify that the value is in the list of choices, if defined
            if attribute.choices:

                # Walk through the list, if the attribute is one.
                if isinstance(attr_value, list):
                    for val in attr_value:
                        if val not in attribute.choices:
                            error = f'{val} is not one of the available choices: {attribute.choices}'
                            verify_error_info.add_attribute_error(name=attr_name, error=error)
                else:
                    if attr_value not in attribute.choices:
                        error = f'{attr_value} is not one of the available choices: {attribute.choices}'
                        verify_error_info.add_attribute_error(name=attr_name, error=error)

            if attribute.required and attr_value is None:
                verify_error_info.add_attribute_error(name=attr_name, error='Attribute is required but value is None')

            if attribute.dynamic and attr_value is not None:
                verify_error_info.add_attribute_error(name=attr_name, error='Attribute is dynamic value can not be specified.')

            if attribute.number_range and attribute.number_range.in_range(attr_value) is False:
                attr_min = attribute.number_range.min
                attr_max = attribute.number_range.max

                verify_error_info.add_attribute_error(
                    name=attr_name, error=f'Attribute value ({attr_value}) not in range [{attr_min} - {attr_max}].')

            # Make sure that the attribute type is allowed
            if attribute.types and attr_value:
                for type_check in attribute.types:
                    if inspect.isclass(attr_value):
                        class_type = attr_value
                    else:
                        class_type = type(attr_value)

                    if issubclass(class_type, type_check) is False:
                        verify_error_info.add_attribute_error(name=attr_name,
                                                              error=f'value of type {type(attr_value)} not allowed')

        if verify_error_info.attribute_errors:
            raise verify_error_info

    @classmethod
    @abstractmethod
    def version(cls) -> ResourceVersion:
        """Fetch the versioning data for the resource. This should be overridden by the provider."""

    def saved_version(self) -> ResourceVersion:
        """Return the persisted provider version OR the current one."""
        if self._saved_version:
            return self._saved_version

        return self.version()

    def get_attribute(self, name) -> StackzillaAttribute:
        """Given an attribute name, fetch the StackzillaAttribute object.

        Args:
            name (_type_): Attribute name within the resource class definition

        Raises:
            AttributeNotFound: Raised if the attribute is not found

        Returns:
            StackzillaAttribute: The StackzillaAttribute object
        """
        try:
            return getattr(self.__class__, name)
        except AttributeError as exc:
            raise AttributeNotFound from exc

    def get_attribute_value(self, name) -> Any:
        """Given an attribute name, fetch the value. If there is a default value, and no value exists, return that.

        Args:
            name (_type_): Name of the attribute to query

        Returns:
            Any: The value for the attribute.

        Raises:
            AttributeError: Raised when "name" is not found.
        """
        return getattr(self, name)

    @property
    def attributes(self) -> Dict[str, StackzillaAttribute]:
        """Fetch all of the StackzillaAttribute objects defined for the class.

        Returns:
            Dict[str, StackzillaAttribute]: List of StackzillaAttribute objects on the class.
        """
        results = {}

        # Find all of the class variables (NOT instance vars) that derive from the StackzillaAttribute class
        for name, obj in inspect.getmembers(self.__class__):
            if isinstance(obj, StackzillaAttribute):
                # Save off the StackzillaAttribute in the results
                results[name] = obj

                # Grab the value of the attribute from our own dictionary, storing it into the StackzillaAttribute instance itself
                results[name].value = self.__dict__.get(name, obj.default)

        return results

    def on_attributes_modified(self, attributes: List[AttributeModified]) -> None:
        """Handler that is called when attributes have been modified.

        Args:
            attributes (List[AttributeModified]): A list of modifications
        """

    def _on_attribute_modified(self, attribute_name: str, previous_value: Any, new_value: Any) -> bool:
        """Invokes the modify method for an attribute (if defined).

        Args:
            attribute_name (str): The name of the attribute
            previous_value (Any): The value of the attribute before modification
            new_value (Any): The value of the attribute after modification

        Returns:
            bool: True if the modified handler is present, and was called
        """
        # The magic method is <parameter_name>_modified()
        method_name = f'{attribute_name}_modified'

        # Check if the method is defined, and that it's actually a method!
        if hasattr(self, method_name) and callable(getattr(self, method_name)):
            method = getattr(self, method_name)

            # Invoke the modify method
            method(previous_value=previous_value, new_value=new_value)
            return True

        # There was no *_modified() method
        return False

    def load_from_db(self, silent_fail: bool=False):
        """Import all of the attribute values from the database."""
        try:
            for attribute_name in self.attributes:
                value = StackzillaDB.db.get_attribute(resource=self, name=attribute_name)
                setattr(self, attribute_name, value)
        except ResourceNotFound as err:
            if silent_fail is True:
                return

            raise err

        # Load the version number from the database
        self._saved_version = StackzillaDB.db.get_resource_version(resource=self)

    def create_in_db(self):
        """Persist the resource, and its attributes, in the database."""
        StackzillaDB.db.create_resource(resource=self)

        for name in self.attributes:
            StackzillaDB.db.create_attribute(resource=self, name=name, value=getattr(self, name))

    def delete_from_db(self):
        """Delete the resource, and all its attributes, from the database."""
        for name in self.attributes:
            try:
                StackzillaDB.db.delete_attribute(resource=self, name=name)
            except ResourceNotFound:
                self._core_logger.debug(message='Resource not found during attribute deletion',
                                        extra={'resource_name': self.path()})

        # If the path for the resource is rooted with the database prefix, replace it with '.'
        try:
            StackzillaDB.db.delete_resource(path=self.path())
        except ResourceNotFound:
            self._core_logger.debug(message='Resource not found during deletion',
                                    extra={'resource_name': self.path()})
