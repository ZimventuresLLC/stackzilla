"""Abstract base class for all database interfaces."""
from abc import ABC, abstractmethod
from typing import Any, List, Type

from stackbot.attribute import StackBotAttribute
from stackbot.resource import StackBotResource


class StackBotDBBase(ABC):
    """Interface definition for concrete database implementations."""

    # This class variable is setup once and then referenced by the entire
    # application to determine which database interface to use
    provider = Type['StackBotDBBase']

    def __init__(self, name: str) -> None:
        """Base database class constructor.

        Args:
            name (str): The name of the database. Implementation specific.
        """
        super().__init__()
        self._name = name

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

    @abstractmethod
    def create_resource(self, resource: StackBotResource):
        """Create a new resource in the database.

        Args:
            resource (StackBotResource): The resource to serialize to the database
        """

    @abstractmethod
    def get_resource(self, name: str) -> StackBotResource:
        """Query the database for a single resource.

        Args:
            name (str): Full python path to the resource. Ex: servers.MyWebServer

        Returns:
            StackBotResource: The deserielized resource
        """

    @abstractmethod
    def get_all_resources(self) -> List[StackBotResource]:
        """Fetch all of the available resources from the database.

        Returns:
            List[StackBotResource]: List of StackBotResource objects
        """

    @abstractmethod
    def update_resource(self, resource: StackBotResource) -> None:
        """Update the values for an existing resource.

        Args:
            resource (StackBotResource): The resource to update
        """

    @abstractmethod
    def delete_resource(self, name: str) -> None:
        """Delete a single StackBotResource item in the database.

        Args:
            name (str): Name of the StackBotResource item to delete
        """

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
