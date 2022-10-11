"""Base class for all user defined resources."""
from abc import abstractmethod
from dataclasses import dataclass
import inspect
from typing import Any, Dict, List

from stackbot.attribute import StackBotAttribute
from stackbot.database.base import StackBotDB
from stackbot.database.exceptions import AttributeNotFound
from stackbot.utils.constants import DB_BP_PREFIX

@dataclass
class ResourceVersion:
    """Data structure to represent versioning information for a StackBotResource"""
    major: int
    minor: int
    build: int
    name: str

class StackBotResource:
    """Base class for all user defined resources."""

    def __init__(self) -> None:
        """Base constructor for all StackBot resource types."""

    @classmethod
    def path(cls) -> str:
        """A unique name (within the blueprint) for this resource."""
        path = f'{cls.__module__}.{cls.__name__}'
        if path.startswith(DB_BP_PREFIX):
            path = path.replace(DB_BP_PREFIX, '.')
            
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

    @abstractmethod
    def verify(self) -> None:
        """Perform verification logic for the resource."""

    @classmethod
    @abstractmethod
    def version(cls) -> ResourceVersion:
        """Fetch the versioning data for the resource. This should be overridden by the provider."""

    def get_attribute(self, name) -> StackBotAttribute:
        """Given an attribute name, fetch the StackBotAttribute object

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