"""SQLite database provider."""
import os
import sqlite3
from sqlite3 import Connection, Cursor
from typing import Any, List, Optional

from stackbot.database.base import StackBotDBBase
from stackbot.database.exceptions import (DatabaseExists, DatabaseNotFound,
                                          MetadataKeyNotFound)
from stackbot.logging.core import CoreLogger
from stackbot.resource import StackBotResource


class StackBotSQLiteDB(StackBotDBBase):
    """Concrete implementation of SQLite."""

    MetadataTableName = 'metadata'

    def __init__(self, name: str) -> None:
        """An unremarkably boring constructor.

        Args:
            name (str): Full path to the database file. Name will be appended with ".db"
        """
        super().__init__(name=f'{name}.db')

        self._db: Optional[Connection] = None
        self._cursor: Optional[Cursor] = None
        self._logger = CoreLogger(component='StackBotSQLiteDB')

    def create(self) -> None:
        """Create the database file.

        Raises:
            DatabaseExists: Raised if the file already exists.
        """
        # If the database already exists, raise an exception
        if os.path.exists(self.name):
            raise DatabaseExists

        self._db = sqlite3.connect(self.name)
        self._cursor = self._db.cursor()

        # Create the metadata store
        self._db.execute(f'CREATE TABLE IF NOT EXISTS {StackBotSQLiteDB.MetadataTableName} (key text unique, value text)')

    def delete(self) -> None:
        """Delete the sqlite databse file."""
        self._close()

        if os.path.exists(self.name):
            self._logger.debug(f'Unlinking database: {self.name}')
            os.unlink(self.name)
        else:
            self._logger.warning(f'Attempted to delete non-existant database: {self.name}')

    def open(self) -> None:
        """Open the database file.

        Raises:
            DatabaseNotFound: Raised if the file does not exist.
        """
        # If the database already exists, raise an exception
        if os.path.exists(self.name) is False:
            raise DatabaseNotFound

        self._db = sqlite3.connect(self.name)
        self._cursor = self._db.cursor()

    def close(self) -> None:
        """Close an existing connection.

        Raises:
            DatabaseNotFound: Raised if there is no existing connection.
        """
        if self._db is None:
            raise DatabaseNotFound

        self._close()

    def _close(self) -> None:
        """Perform a close on the database. Will not fail if there is no database open."""
        if self._db is None:
            return

        self._db.commit()
        self._db.close()
        self._db = None
        self._cursor = None

    def get_metadata(self, key: str) -> Any:
        """Fetch metadata from the database.

        Args:
            key (str): The key to find the value for.

        Raises:
            MetadataKeyNotFound: Raised if the specified key does not exist in the database.

        Returns:
            Any: The value associated with the key.
        """
        item = self._db.execute(f'SELECT value FROM {StackBotSQLiteDB.MetadataTableName}  WHERE key = ?', (key,)).fetchone()

        if item is None:
            raise MetadataKeyNotFound

        return item[0]

    def set_metadata(self, key: str, value: Any) -> None:
        """Set the value for the specified metdata key.

        Args:
            key (str): The unique key to set the value for.
            value (Any): The data to associate with the key.
        """
        self._logger.debug(f'Setting metadata on {key = }')
        self._cursor.execute(f'REPLACE INTO {StackBotSQLiteDB.MetadataTableName} (key, value) VALUES (?,?)', (key, value))
        self._db.commit()

    def delete_metadata(self, key: str) -> None:
        """Delete the specified metadata entry.

        Args:
            key (str): The unique key of the entry to delete.

        Raises:
            MetadataKeyNotFound: Raised if the specified key does not exist.
        """
        if self.check_metadata(key=key) is False:
            raise MetadataKeyNotFound

        self._db.execute(f'DELETE FROM {StackBotSQLiteDB.MetadataTableName}  WHERE key = ?', (key,))
        self._db.commit()

    def check_metadata(self, key: str) -> bool:
        """Query if the specified metadata key exists.

        Args:
            key (str): The unique key to search for.

        Returns:
            bool: True if the key exists, False otherwise
        """
        return self._db.execute(
            f'SELECT 1 FROM {StackBotSQLiteDB.MetadataTableName} WHERE key = ?', (key,)
        ).fetchone() is not None

    def create_resource(self, resource: StackBotResource):
        raise NotImplementedError
        return super().create_resource(resource)

    def delete_resource(self, name: str) -> None:
        raise NotImplementedError
        return super().delete_resource(name)

    def get_all_resources(self) -> List[StackBotResource]:
        raise NotImplementedError
        return super().get_all_resources()

    def get_resource(self, name: str) -> StackBotResource:
        raise NotImplementedError
        return super().get_resource(name)

    def update_resource(self, resource: StackBotResource) -> None:
        raise NotImplementedError
        return super().update_resource(resource)