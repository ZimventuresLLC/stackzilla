"""SQLite database provider."""
import importlib
import json
import os
import sqlite3
from sqlite3 import Connection, Cursor
import sys
from typing import Any, List, Optional

from stackbot.database.base import StackBotDBBase, StackBotDB
from stackbot.database.exceptions import (
    AttributeNotFound, BlueprintModuleNotFound, CreateAttributeFailure, CreateBlueprintModuleFailure, CreateResourceFailure, DatabaseExists,
    DatabaseNotFound, DuplicateAttribute, DuplicateBlueprintModule, MetadataKeyNotFound, ResourceNotFound
)
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

        # Set ourselves to the singleton member
        # Adding a special pytest check here for the unit test case. For unit testing there is no caching
        if 'pytest' not in sys.argv[0]:
            assert StackBotDB.db is None
            StackBotDB.db = self

    def create(self, in_memory: bool = False) -> None:
        """Create the database file.

        Args:
            in_memory (bool): If true, the database will only exist in memory. Defaults to False

        Raises:
            DatabaseExists: Raised if the file already exists.
        """

        if in_memory:
            self._db = sqlite3.connect('file::memory:?cache=shared')
        else:
            # If the database already exists, raise an exception
            if os.path.exists(self.name):
                raise DatabaseExists

            self._db = sqlite3.connect(self.name)

        # Access query results by column ID instead of by index
        self._db.row_factory = sqlite3.Row

        self._cursor = self._db.cursor()

        # Create the metadata store
        self._db.execute(f'CREATE TABLE IF NOT EXISTS {StackBotSQLiteDB.MetadataTableName} (key text unique, value text)')

        # Create the StackBotResource table
        self._db.execute('CREATE TABLE StackBotResource(id INTEGER PRIMARY KEY, path TEXT UNIQUE)')

        # Create the StackBotAttribute table
        create_attribute_sql = """CREATE TABLE StackBotAttribute(
                                  "id" INTEGER PRIMARY KEY,
                                  "name" TEXT,
                                  "value" BLOB,
                                  "resource_id" INTEGER,
                                  FOREIGN KEY(resource_id) REFERENCES StackBotResource(id) ON DELETE CASCADE)"""
        self._db.execute(create_attribute_sql)

        # Create the blueprint module table
        create_blueprint_module_sql = """CREATE TABLE StackBotBlueprintModule(
                                         "ID" INTEGER PRIMARY KEY,
                                         "path" TEXT UNIQUE,
                                         "data" TEXT)"""
        self._db.execute(create_blueprint_module_sql)

        self._db.commit()

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

        # Access query results by column ID instead of by index
        self._db.row_factory = sqlite3.Row

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

        value = json.loads(item[0])
        return value

    def set_metadata(self, key: str, value: Any) -> None:
        """Set the value for the specified metdata key.

        Args:
            key (str): The unique key to set the value for.
            value (Any): The data to associate with the key.
        """

        json_value = json.dumps(value)
        self._logger.debug(f'Setting metadata on {key = }')
        self._cursor.execute(f'REPLACE INTO {StackBotSQLiteDB.MetadataTableName} (key, value) VALUES (?,?)', (key, json_value))
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

    def create_resource(self, resource: StackBotResource) -> None:
        """Create a new StackBotResource in the database.

        Args:
            resource (StackBotResource): The resource to create.

        Raises:
            CreateResourceFailure: Raised if a creation error occurs.
        """
        self._logger.debug(f'INSERT {resource.path()}')
        try:
            self._db.execute('INSERT INTO StackBotResource (path) VALUES (?)', (resource.path(),))
            self._db.commit()
        except sqlite3.IntegrityError as exc:
            raise CreateResourceFailure() from exc

    def delete_resource(self, path: str) -> None:
        """Delete the specified resource from the database.

        Args:
            path (str): The full Python path of the resource. Available via <resource>.path.

        Raises:
            ResourceNotFound: Raised if the resource specified by path does not exist in the database.
        """
        resource_id: int = self._resource_id_from_path(path=path)
        self._db.execute('DELETE FROM StackBotResource WHERE id=:resource_id', {'resource_id': resource_id})

    def get_all_resources(self) -> List[StackBotResource]:
        results: List[StackBotResource] = []

        cursor = self._db.execute('SELECT * FROM StackBotResource')

        for result in cursor.fetchall():
            # Fetch a StackBotResource object WITH its parameters field populated
            results.append(self.get_resource(path=result['path']))

        return results

    def get_resource(self, path: str) -> StackBotResource:
        """Fetch a resource from the database

        Args:
            path (str): The full python path to the resource within the blueprint

        Returns:
            StackBotResource: An instance of the derrived StackBotResource class

        Raises:
            ResourceNotFound: If the specified path does not exist
        """
        resource_id = self._resource_id_from_path(path=path)

        # Break apart the path into the module and class components
        # example "a.b.c.MyClass" where "a.b.c" is the module and "MyClass" is the class naame
        class_name = path.split('.')[-1]
        module_name = '.'.join(path.split('.')[:-1])

        # It is assumed that the blueprint has ALREADY been imported and that this module can be loaded
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)

        # TODO: Populate the class with the parameters
        return class_()


        # cursor = self._db.execute('SELECT * FROM StackBotDBParameter WHERE resource_id=:resource_id', {'resource_id': resource_id})

    def update_resource(self, resource: StackBotResource) -> None:
        raise NotImplementedError
        return super().update_resource(resource)

    def create_attribute(self, resource: StackBotResource, name: str, value: Any):
        """Adds a new attribute to the database.

        Args:
            name (str): The name of the attribute to set the value for
            value (Any): The value to assign to the attribute
        """
        resource_id = self._resource_id_from_path(resource.path())

        # Ensure that an attribute with the resource_id/name combo doesn't alreadt exist
        try:
            self._get_attribute_id(resource=resource, name=name)

            # If we get here, the attribute was found - this is bad!
            raise DuplicateAttribute

        except AttributeNotFound:
            pass

        sql = """INSERT INTO StackBotAttribute ("resource_id",
                                                "name",
                                                "value")
                                                VALUES (:resource_id, :name, :value)"""
        insert_data = {
            'name': name,
            'value': value,
            'resource_id': resource_id
        }

        try:
            self._db.execute(sql, insert_data)
            self._db.commit()
        except sqlite3.IntegrityError as exc:
            raise CreateAttributeFailure() from exc

    def delete_attribute(self, resource: StackBotResource, name: str):
        """Delete an attribute previously added to the database.

        Args:
            resource (StackBotResource): The resource that the attribute belongs to
            name (str): The attribute name to delete

        Raises:
            AttributeNotFound: Raised if the attribute is not found in the database
        """

        attribute_id = self._get_attribute_id(resource=resource, name=name)

        delete_sql = 'DELETE FROM StackBotAttribute WHERE id=:attribute_id'
        self._db.execute(delete_sql, {'attribute_id': attribute_id})

    def update_attribute(self, resource: StackBotResource, name: str, value: Any):
        """Update a previously created attribute.

        Args:
            resource (StackBotResource): The resource that the attribute belongs to
            name (str): The attribute name to update
            value (Any): The new value to assign to the attribute

        Raises:
            AttributeNotFound: Raised if the attribute is not found in the database

        """
        attribute_id = self._get_attribute_id(resource=resource, name=name)

        update_sql = """UPDATE StackBotAttribute SET
                        "value"=:value
                        WHERE id=:attribute_id"""

        update_data = {
            "value": value,
            "attribute_id": attribute_id,
            "name": name
        }

        self._db.execute(update_sql, update_data)

    def get_attribute(self, resource: StackBotResource, name: str) -> Any:
        """Fetch a single attribute from the dataase.

        Args:
            resource (StackBotResource): The StackBotResource that the attribute belongs to
            name (str): Name of the attribute as it's definined in the StackBotResource class

        Raises:
            AttributeNotFound: Raised if the attribute is not found in the database

        Returns:
            Any: The value corresponding to the specified attribute name
        """
        resource_id = self._resource_id_from_path(path=resource.path())

        select_sql = 'SELECT * FROM StackBotAttribute WHERE resource_id=:resource_id AND name=:name'
        select_args = {'resource_id': resource_id, 'name': name}
        cursor = self._db.execute(select_sql, select_args )

        row = cursor.fetchone()
        if row is None:
            raise AttributeNotFound

        return row['value']

    def create_blueprint_module(self, path: str, data: Optional[str] = None) -> None:
        """Create a blueprint module within the database.

        Args:
            path (str): The Python path to the module
            data (str): Contents of the module file. If not specified, the module is actually a package. Defaults to None.

        Raises:
            CreateBlueprintModuleFailure: Raised when the database insertion fails.
        """
        try:
            self._get_blueprint_module_id(path=path)
            raise DuplicateBlueprintModule
        except BlueprintModuleNotFound:
            pass

        sql = """INSERT INTO StackBotBlueprintModule ("path", "data") VALUES (:path, :data)"""
        insert_data = {
            'path': path,
            'data': data
        }

        try:
            self._db.execute(sql, insert_data)
            self._db.commit()
        except sqlite3.IntegrityError as exc:
            raise CreateBlueprintModuleFailure() from exc

    def get_blueprint_module(self, path: str) -> str:
        """Fetch the module data for a specified Python path.

        Args:
            path (str): The full Python path to the module

        Returns:
            str: Contents of the module file.

        Raises:
            BlueprintModuleNotFound: Raised when the path does not exist.
        """

        select_sql = 'SELECT * FROM StackBotBlueprintModule WHERE path=:path'
        cursor = self._db.execute(select_sql, {'path': path})
        row = cursor.fetchone()
        if row is None:
            raise BlueprintModuleNotFound

        return row['data']

    def get_blueprint_modules(self) -> List[str]:
        """Query all of the available modules.

        Returns:
            List[str]: A list of Python paths, each represenging a module
        """

        results: List[str] = []
        select_sql = 'SELECT * FROM StackBotBlueprintModule'
        cursor = self._db.execute(select_sql)
        for row in cursor.fetchall():
            results.append(row['path'])

        return results


    def update_blueprint_module(self, path: str, data: str) -> None:
        """Update the contents for an existing module.

        Args:
            path (str): Full Python path to the module
            data (str): Contents of the module file

        Raises:
            BlueprintModuleNotFound: Raised when the path does not exist.
        """
        blueprint_module_id = self._get_blueprint_module_id(path=path)

        update_sql = """UPDATE StackBotBlueprintModule SET
                        "data"=:data
                        WHERE id=:id"""

        update_data = {
            "data": data,
            "id": blueprint_module_id
        }

        self._db.execute(update_sql, update_data)


    def delete_blueprint_module(self, path: str) -> None:
        """Delete an existing module

        Args:
            path (str): Full Python path to the module

        Raises:
            BlueprintModuleNotFound: Raised when the path does not exist.
        """
        blueprint_module_id = self._get_blueprint_module_id(path=path)
        delete_sql = 'DELETE FROM StackBotBlueprintModule WHERE id=:id'
        self._db.execute(delete_sql, {'id': blueprint_module_id})

    def delete_all_blueprint_modules(self) -> None:
        """Delete all of the blueprints from the database."""
        delete_sql = 'DELETE FROM StackBotBlueprintModule'
        self._db.execute(delete_sql)

    def _get_blueprint_module_id(self, path: str) -> int:
        """Fetch the row ID for a given blueprint module, based on the provided path.

        Args:
            path (str): Full Python path to the blueprint module

        Raises:
            BlueprintModuleNotFound: Raised if the module is not found

        Returns:
            int: The row ID for the module
        """
        select_sql = 'SELECT * FROM StackBotBlueprintModule WHERE path=:path'
        cursor = self._db.execute(select_sql, {'path': path})
        row = cursor.fetchone()
        if row is None:
            raise BlueprintModuleNotFound

        return row['id']

    def _get_attribute_id(self, resource: StackBotResource, name: str) -> int:
        """Fetch the database ID for the requested attribute
        TODO: Can this be cached?

        Args:
            resource (StackBotResource): The resource that the attibute belongs to.
            name (str): Name of the attribute to fetch, as definined in the resource class

        Raises:
            AttributeNotFound: Raised if the attribute is not found

        Returns:
            int: Database ID of the StackBotResource row
        """
        resource_id = self._resource_id_from_path(path=resource.path())

        select_sql = 'SELECT * FROM StackBotAttribute WHERE resource_id=:resource_id AND name=:name'
        select_args = {'resource_id': resource_id, 'name': name}
        cursor = self._db.execute(select_sql, select_args )

        row = cursor.fetchone()
        if row is None:
            raise AttributeNotFound

        return row['id']

    def _resource_id_from_path(self, path: str) -> int:
        """Helper method to fetch the ID of the resource by its Python path
        TODO: Can this be cached?
        Args:
            path (str): Python path of the resource within the blueprint

        Raises:
            ResourceNotFound: Raised if the path is not found

        Returns:
            int: The SQLite ID of the row for the resource
        """
        with self._db:
            cursor = self._db.execute('SELECT * FROM StackBotResource WHERE path=:path', {'path': path})
            row = cursor.fetchone()
            if row is None:
                raise ResourceNotFound()

            return row['id']
