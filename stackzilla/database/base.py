"""Abstract base class for all database interfaces."""
import typing
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type

if typing.TYPE_CHECKING:
    from stackzilla.resource import StackzillaResource

# pylint: disable=too-many-public-methods
class StackzillaDBBase(ABC):
    """Interface definition for concrete database implementations."""

    # This class variable is setup once and then referenced by the entire
    # application to determine which database interface to use
    provider: Type['StackzillaDBBase'] = None
    static_name: str = None

    def __init__(self, name: str) -> None:
        """Base database class constructor.

        Args:
            name (str): The name of the database. Implementation specific.
        """
        super().__init__()
        self._name = name
        StackzillaDBBase.static_name = name

    @property
    def name(self):
        """The name previously passed into the constructor."""
        return self._name

    @abstractmethod
    def create(self) -> None:
        """Create a new database.

        Raises:
            DatabaseExists: If the database already exists
        """

    @abstractmethod
    def delete(self) -> None:
        """Delete an existing database.

        Raises:
            DatabaseNotFound: When the specified database does not exist.
        """

    @abstractmethod
    def open(self) -> None:
        """Open an existing database.

        Raises:
            DatabaseNotFound: When the specified database name is not found.
        """

    @abstractmethod
    def close(self) -> None:
        """Close an existing dataabase connection.

        Raises:
            DatabaseNotFound: When there is no open database connection.
        """

    ###############################################################################
    # Methods for interacting with StackzillaResource objects
    ###############################################################################
    @abstractmethod
    def create_resource(self, resource: 'StackzillaResource') -> None:
        """Create a new resource in the database.

        Args:
            resource (StackzillaResource): The resource to serialize to the database
        """

    @abstractmethod
    def get_resource(self, path: str) -> 'StackzillaResource':
        """Query the database for a single resource.

        Args:
            path (str): Full python path to the resource. Ex: servers.MyWebServer

        Returns:
            StackzillaResource: The deserielized resource
        """

    @abstractmethod
    def get_all_resources(self) -> List['StackzillaResource']:
        """Fetch all of the available resources from the database.

        Returns:
            List[StackzillaResource]: List of StackzillaResource objects
        """

    @abstractmethod
    def update_resource(self, resource: 'StackzillaResource') -> None:
        """Update the values for an existing resource.

        Args:
            resource (StackzillaResource): The resource to update
        """

    @abstractmethod
    def delete_resource(self, path: str) -> None:
        """Delete a single StackzillaResource item in the database.

        Args:
            path (str): Python path of the StackzillaResource item to delete
        """

    ###############################################################################
    # Methods for interacting with StackzillaAttribute objects
    ###############################################################################
    @abstractmethod
    def create_attribute(self, resource: 'StackzillaResource', name: str, value: Any):
        """Adds a new attribute to the database.

        Args:
            resource (StackzillaResource): The parent resource for the attribute being created
            name (str): The name of the attribute to create
            value (Any): The value to assign to the newly created attribute
        """

    @abstractmethod
    def get_attribute(self, resource: 'StackzillaResource', name: str) -> Any:
        """Fetch the value for an attribute.

        Args:
            resource (StackzillaResource): The name of the resource to fetch the attribute for
            name (str): The name of the attribute to fetch the value for

        Returns:
            Any: The attribute value.

        Raises:
            AttributeNotFound: Raised if the attribute is not found.
        """

    @abstractmethod
    def delete_attribute(self, resource: 'StackzillaResource', name: str):
        """Delete an attribute previously added to the database.

        Args:
            resource (StackzillaResource): The resource that the attribute belongs to
            name (str): The name of the attribute to delete
        """

    @abstractmethod
    def update_attribute(self, resource: 'StackzillaResource', name: str, value: Any):
        """Update a previously created attribute.

        Args:
            resource (StackzillaResource): The resource that the attribute belongs to
            name (str): The attribute name to update
            value (Any): The new value to assign to the attribute
        """

    ###############################################################################
    # Methods for interacting with the meatadata facility
    ###############################################################################
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """Set the value for the specified metadata key.

        Args:
            key (str): Name of the metadata key
            value (Any): Metadata item value
        """

    @abstractmethod
    def get_metadata(self, key: str) -> Any:
        """Fetch the metadata value for the given key.

        Args:
            key (str): Key to fetch the metadata value for.

        Returns:
            Any: The value corresponding to the specified name

        Raises:
            MetadataKeyNotFound: Raised if key is not found in the database
        """

    @abstractmethod
    def delete_metadata(self, key: str) -> None:
        """Delete the metadata key, if found.

        Args:
            key (str): Name of the metadata key/value pair to delete

        Raises:
            MetadataKeyNotFound: Raised if key is not found in the database
        """

    @abstractmethod
    def check_metadata(self, key: str) -> bool:
        """Test if a metadata key exists.

        Args:
            key (str): Name of the metadata key to query for

        Returns:
            bool: True if the metadata key exists, False otherwise
        """

    ###############################################################################
    # CRUD methods for working with blueprint modules and packages
    ###############################################################################
    @abstractmethod
    def create_blueprint_module(self, path: str, data: Optional[str] = None) -> None:
        """Create a blueprint module within the database.

        Args:
            path (str): The Python path to the module
            data (str): Contents of the module file. If not specified, the module is actually a package. Defaults to None.
        """

    @abstractmethod
    def get_blueprint_module(self, path: str) -> str:
        """Fetch the module data for a specified Python path.

        Args:
            path (str): The full Python path to the module

        Returns:
            str: Contents of the module file.
        """

    @abstractmethod
    def get_blueprint_modules(self) -> List[str]:
        """Query all of the available modules.

        Returns:
            List[str]: A list of Python paths, each represenging a module
        """

    @abstractmethod
    def update_blueprint_module(self, path: str, data: str) -> None:
        """Update the contents for an existing module.

        Args:
            path (str): Full Python path to the module
            data (str): Contents of the module file
        """

    @abstractmethod
    def delete_blueprint_module(self, path: str) -> None:
        """Delete an existing module.

        Args:
            path (str): Full Python path to the module
        """

    @abstractmethod
    def delete_all_blueprint_modules(self) -> None:
        """Delete all of the blueprint modules."""

    @abstractmethod
    def create_blueprint_package(self, path: str) -> None:
        """Create a new blueprint package.

        Args:
            path (str): Full Python path of the package
        """

    @abstractmethod
    def delete_blueprint_package(self, path: str) -> None:
        """Delete a blueprint package from the database.

        Args:
            path (str): Full Python path to the package
        """

    @abstractmethod
    def delete_all_blueprint_packages(self) -> None:
        """Delete all of the blueprint packages from the database."""

    @abstractmethod
    def get_blueprint_package(self, path: str) -> bool:
        """Queries if a blueprint package exists in the database.

        Args:
            path (str): _description_

        Returns:
            bool: _description_
        """
    @abstractmethod
    def get_blueprint_packages(self) -> List[str]:
        """Fetch a list of all the blueprint packages.

        Returns:
            List[str]: A list of blueprint package names.
        """
# pylint: disable=too-few-public-methods
class StackzillaDB:
    """Globally accessable singleton database object."""

    db: StackzillaDBBase = None
