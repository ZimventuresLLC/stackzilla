"""Base class for all user defined resources."""
import inspect
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from stackbot.attribute import StackBotAttribute
from stackbot.database.base import StackBotDB
from stackbot.database.exceptions import AttributeNotFound
from stackbot.resource.exceptions import ResourceVerifyError
from stackbot.utils.constants import DB_BP_PREFIX


@dataclass
class AttributeModified:
    """Data structure to store attribute modification data."""
    
    name: str
    previous_value: Any
    new_value: Any
    handled: bool = False


@dataclass
class ResourceVersion:
    """Data structure to represent versioning information for a StackBotResource."""

    major: int
    minor: int
    build: int
    name: str

class StackBotResource:
    """Base class for all user defined resources."""

    def __init__(self) -> None:
        """Base constructor for all StackBot resource types."""

    @classmethod
    def path(cls, remove_prefix: bool=False) -> str:
        """A unique name (within the blueprint) for this resource."""
        path = f'{cls.__module__}.{cls.__name__}'

        # Always replace the DB prevfix
        if path.startswith(DB_BP_PREFIX):
            path = path.replace(DB_BP_PREFIX, '.')

        # Optionally remove the '..' prefix
        if remove_prefix:
            path = path.removeprefix('..')

        return path

    def create(self) -> None:
        """Create a new resource."""

    def update(self) -> None:
        """Apply the changes to this resource."""

    def delete(self) -> None:
        """Delete a previously created resource."""

    @abstractmethod
    def depends_on(self) -> List['StackBotResource']:
        """Return a list of other resources that must be applied before this resource can be applied.

        Returns:
            List[StackBotResource]: List of StackBotResource classes that must be applied prior to this resource.
        """
        return []

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
            if attribute.choices and attr_value not in attribute.choices:
                verify_error_info.add_attribute_error(name=attr_name, error=f'{attr_value} is not one of the available choices: {attribute.choices}')

            if attribute.required and attr_value is None:
                verify_error_info.add_attribute_error(name=attr_name, error='Attribute is required but value is None')

            if attribute.dynamic and attr_value is not None:
                verify_error_info.add_attribute_error(name=attr_name, error='Attribute is dynamic value can not be specified.')

        if verify_error_info.attribute_errors:
            raise verify_error_info

    @classmethod
    @abstractmethod
    def version(cls) -> ResourceVersion:
        """Fetch the versioning data for the resource. This should be overridden by the provider."""

    def get_attribute(self, name) -> StackBotAttribute:
        """Given an attribute name, fetch the StackBotAttribute object.

        Args:
            name (_type_): Attribute name within the resource class definition

        Raises:
            AttributeNotFound: Raised if the attribute is not found

        Returns:
            StackBotAttribute: The StackBotAttribute object
        """
        # TODO: Is there a better way to find this?
        for attr_name, obj in inspect.getmembers(self.__class__):
            if attr_name == name:
                return obj

        raise AttributeNotFound

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
    def attributes(self) -> Dict[str, StackBotAttribute]:
        """Fetch all of the StackBotAttribute objects defined for the class.

        Returns:
            Dict[str, StackBotAttribute]: List of StackBotAttribute objects on the class.
        """
        results = {}

        # Find all of the class variables (NOT instance vars) that derive from the StackBotAttribute class
        for name, obj in inspect.getmembers(self.__class__):
            if isinstance(obj, StackBotAttribute):
                # Save off the StackBotAttribute in the results
                results[name] = obj

                # Grab the value of the attribute from our own dictionary, storing it into the StackBotAttribute instance itself
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

        return False

    def load_from_db(self):
        """Import all of the attribute values from the database."""
        for attribute_name in self.attributes:
            value = StackBotDB.db.get_attribute(resource=self, name=attribute_name)
            setattr(self, attribute_name, value)

    def create_in_db(self):
        """Persist the resource, and its attributes, in the database."""
        StackBotDB.db.create_resource(resource=self)

        for name in self.attributes:
            StackBotDB.db.create_attribute(resource=self, name=name, value=getattr(self, name))

    def delete_from_db(self):
        """Delete the resource, and all its attributes, from the database."""
        for name in self.attributes:
            StackBotDB.db.delete_attribute(resource=self, name=name)

        # If the path for the resource is rooted with the database prefix, replace it with '.'
        resource_path = self.path()
        StackBotDB.db.delete_resource(path=resource_path)
