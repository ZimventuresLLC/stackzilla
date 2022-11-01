"""SQLite database provider."""
import base64
import importlib
import json
import os
import pickle
import sqlite3
import sys
from sqlite3 import Connection, Cursor
from typing import Any, List, Optional

from stackzilla.database.base import StackzillaDB, StackzillaDBBase
from stackzilla.database.exceptions import (AttributeNotFound,
                                            BlueprintModuleNotFound,
                                            BlueprintPackageNotFound,
                                            CreateAttributeFailure,
                                            CreateBlueprintModuleFailure,
                                            CreateBlueprintPackageFaiure,
                                            CreateResourceFailure,
                                            DatabaseExists, DatabaseNotFound,
                                            DatabaseNotOpen,
                                            DuplicateAttribute,
                                            DuplicateBlueprintModule,
                                            DuplicateBlueprintPackage,
                                            MetadataKeyNotFound,
                                            ResourceNotFound)
from stackzilla.logger.core import CoreLogger
from stackzilla.resource import StackzillaResource
from stackzilla.resource.base import ResourceVersion


# pylint: disable=too-many-public-methods
class StackzillaSQLiteDB(StackzillaDBBase):
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
        self._logger = CoreLogger(component='StackzillaSQLiteDB')

        # Set ourselves to the singleton member
        # Adding a special pytest check here for the unit test case. For unit testing there is no caching
        if 'pytest' not in sys.argv[0]:
            assert StackzillaDB.db is None

        StackzillaDB.db = self

    @property
    def connection(self) -> Connection:
        """Fetch the DB connection object."""
        if self._db is None:
            raise DatabaseNotOpen

        return self._db

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
        self._db.execute(f'CREATE TABLE IF NOT EXISTS {StackzillaSQLiteDB.MetadataTableName} (key text unique, value text)')

        # Create the StackzillaResource table
        self._db.execute("""CREATE TABLE StackzillaResource(
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE,
            version_major INTEGER,
            version_minor INTEGER,
            version_build INTEGER,
            version_name TEXT)""")

        # Create the StackzillaAttribute table
        create_attribute_sql = """CREATE TABLE StackzillaAttribute(
                                  "id" INTEGER PRIMARY KEY,
                                  "name" TEXT,
                                  "value" BLOB,
                                  "resource_id" INTEGER,
                                  FOREIGN KEY(resource_id) REFERENCES StackzillaResource(id) ON DELETE CASCADE)"""
        self._db.execute(create_attribute_sql)

        # Create the blueprint module table
        create_blueprint_module_sql = """CREATE TABLE StackzillaBlueprintModule(
                                         "ID" INTEGER PRIMARY KEY,
                                         "path" TEXT UNIQUE,
                                         "data" TEXT)"""
        self._db.execute(create_blueprint_module_sql)

        # Create the blueprint package table
        create_blueprint_package_sql = """CREATE TABLE StackzillaBlueprintPackage(
                                         "ID" INTEGER PRIMARY KEY,
                                         "path" TEXT UNIQUE)"""
        self._db.execute(create_blueprint_package_sql)

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
            DatabaseNotOpen: Raised if there is no existing connection.
        """
        if self._db is None:
            raise DatabaseNotOpen

        self._close()

    def _close(self) -> None:
        """Perform a close on the database. Will not fail if there is no database open."""
        if self._db is None:
            return

        self.connection.commit()
        self.connection.close()
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
        sql = f'SELECT value FROM {StackzillaSQLiteDB.MetadataTableName}  WHERE key = ?'
        item = self.connection.execute(sql, (key,)).fetchone()

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
        self._cursor.execute(f'REPLACE INTO {StackzillaSQLiteDB.MetadataTableName} (key, value) VALUES (?,?)', (key, json_value))
        self.connection.commit()

    def delete_metadata(self, key: str) -> None:
        """Delete the specified metadata entry.

        Args:
            key (str): The unique key of the entry to delete.

        Raises:
            MetadataKeyNotFound: Raised if the specified key does not exist.
        """
        if self.check_metadata(key=key) is False:
            raise MetadataKeyNotFound

        self.connection.execute(f'DELETE FROM {StackzillaSQLiteDB.MetadataTableName}  WHERE key = ?', (key,))
        self.connection.commit()

    def check_metadata(self, key: str) -> bool:
        """Query if the specified metadata key exists.

        Args:
            key (str): The unique key to search for.

        Returns:
            bool: True if the key exists, False otherwise
        """
        return self.connection.execute(
            f'SELECT 1 FROM {StackzillaSQLiteDB.MetadataTableName} WHERE key = ?', (key,)
        ).fetchone() is not None

    def create_resource(self, resource: StackzillaResource) -> None:
        """Create a new StackzillaResource in the database.

        Args:
            resource (StackzillaResource): The resource to create.

        Raises:
            CreateResourceFailure: Raised if a creation error occurs.
        """
        self._logger.debug(f'INSERT {resource.path()}')
        try:
            create_sql = """INSERT INTO StackzillaResource
            ("path", "version_major", "version_minor", "version_build", "version_name")
            VALUES (:path, :version_major, :version_minor, :version_build, :version_name)"""

            version = resource.version()
            create_params = {
                'path': resource.path(),
                'version_major': version.major,
                'version_minor': version.minor,
                'version_build': version.build,
                'version_name': version.name
            }

            self.connection.execute(create_sql, create_params)
            self.connection.commit()
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
        self.connection.execute('DELETE FROM StackzillaResource WHERE id=:resource_id', {'resource_id': resource_id})
        self.connection.commit()

    def get_all_resources(self) -> List[StackzillaResource]:
        """Fetch all of the resources available in the databae.

        Returns:
            List[StackzillaResource]: A list of StackzillaResource objects
        """
        results: List[StackzillaResource] = []

        cursor = self.connection.execute('SELECT * FROM StackzillaResource')

        for result in cursor.fetchall():
            # Fetch a StackzillaResource object WITH its parameters field populated
            results.append(self.get_resource(path=result['path']))

        return results

    def get_resource(self, path: str) -> StackzillaResource:
        """Fetch a resource from the database.

        Args:
            path (str): The full python path to the resource within the blueprint

        Returns:
            StackzillaResource: An instance of the derrived StackzillaResource class

        Raises:
            ResourceNotFound: If the specified path does not exist
        """
        # Verify that the resource is availbale (ResourceNotFound will be raised if it isn't)
        self._resource_from_path(path=path)

        # Break apart the path into the module and class components
        # example "a.b.c.MyClass" where "a.b.c" is the module and "MyClass" is the class naame
        class_name = path.split('.')[-1]
        module_name = '.'.join(path.split('.')[:-1])

        # It is assumed that the blueprint has ALREADY been imported and that this module can be loaded
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)

        obj = class_()

        # Load all of the attribute values from the database
        obj.load_from_db()

        return obj

    def get_resource_version(self, resource: StackzillaResource) -> ResourceVersion:
        """Fetch the resource's persisted version data.

        Args:
            resource (StackzillaResource): The resource to query the version information for.

        Returns:
            ResourceVersion: The version number
        """
        row_data = self._resource_from_path(path=resource.path())

        return ResourceVersion(major=row_data['version_major'],
                               minor=row_data['version_minor'],
                               build=row_data['version_build'],
                               name=row_data['version_name'])

    def update_resource(self, resource: StackzillaResource) -> None:
        """Called to update a resource in the database.

        Args:
            resource (StackzillaResource): The resource to update in the database
        """
        version = resource.version()

        update_sql = """UPDATE StackzillaResource SET
                        "version_major"=:version_major,
                        "version_minor"=:version_minor,
                        "version_build"=:version_build,
                        "version_name"=:version_name
                        WHERE id=:resource_id"""

        update_data = {
            "version_major": version.major,
            "version_minor": version.minor,
            "version_build": version.build,
            "version_name": version.name,
            "resource_id": self._resource_id_from_path(resource.path())
        }

        self.connection.execute(update_sql, update_data)
        self.connection.commit()

    def create_attribute(self, resource: StackzillaResource, name: str, value: Any):
        """Adds a new attribute to the database.

        Args:
        resource (StackzillaResource): The parent resource of the attribute to be created
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

        sql = """INSERT INTO StackzillaAttribute ("resource_id",
                                                "name",
                                                "value")
                                                VALUES (:resource_id, :name, :value)"""

        insert_data = {
            'name': name,
            'value': self._value_encode(value),
            'resource_id': resource_id
        }

        try:
            self.connection.execute(sql, insert_data)
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            raise CreateAttributeFailure(str(exc)) from exc
        except sqlite3.InterfaceError as exc:
            raise CreateAttributeFailure(str(exc)) from exc

    def delete_attribute(self, resource: StackzillaResource, name: str):
        """Delete an attribute previously added to the database.

        Args:
            resource (StackzillaResource): The resource that the attribute belongs to
            name (str): The attribute name to delete

        Raises:
            AttributeNotFound: Raised if the attribute is not found in the database
        """
        attribute_id = self._get_attribute_id(resource=resource, name=name)

        delete_sql = 'DELETE FROM StackzillaAttribute WHERE id=:attribute_id'
        self.connection.execute(delete_sql, {'attribute_id': attribute_id})
        self.connection.commit()

    def update_attribute(self, resource: StackzillaResource, name: str, value: Any):
        """Update a previously created attribute.

        Args:
            resource (StackzillaResource): The resource that the attribute belongs to
            name (str): The attribute name to update
            value (Any): The new value to assign to the attribute

        Raises:
            AttributeNotFound: Raised if the attribute is not found in the database

        """
        attribute_id = self._get_attribute_id(resource=resource, name=name)

        update_sql = """UPDATE StackzillaAttribute SET
                        "value"=:value
                        WHERE id=:attribute_id"""

        update_data = {
            "value": self._value_encode(value),
            "attribute_id": attribute_id,
            "name": name
        }

        self.connection.execute(update_sql, update_data)
        self.connection.commit()

    def get_attribute(self, resource: StackzillaResource, name: str) -> Any:
        """Fetch a single attribute from the dataase.

        Args:
            resource (StackzillaResource): The StackzillaResource that the attribute belongs to
            name (str): Name of the attribute as it's definined in the StackzillaResource class

        Raises:
            AttributeNotFound: Raised if the attribute is not found in the database

        Returns:
            Any: The value corresponding to the specified attribute name
        """
        resource_id = self._resource_id_from_path(path=resource.path())

        select_sql = 'SELECT * FROM StackzillaAttribute WHERE resource_id=:resource_id AND name=:name'
        select_args = {'resource_id': resource_id, 'name': name}
        cursor = self.connection.execute(select_sql, select_args )

        row = cursor.fetchone()
        if row is None:
            raise AttributeNotFound

        return self._value_decode(row['value'])

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

        sql = """INSERT INTO StackzillaBlueprintModule ("path", "data") VALUES (:path, :data)"""
        insert_data = {
            'path': path,
            'data': data
        }

        try:
            self.connection.execute(sql, insert_data)
            self.connection.commit()
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
        select_sql = 'SELECT * FROM StackzillaBlueprintModule WHERE path=:path'
        cursor = self.connection.execute(select_sql, {'path': path})
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
        select_sql = 'SELECT * FROM StackzillaBlueprintModule'
        cursor = self.connection.execute(select_sql)
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

        update_sql = """UPDATE StackzillaBlueprintModule SET
                        "data"=:data
                        WHERE id=:id"""

        update_data = {
            "data": data,
            "id": blueprint_module_id
        }

        self.connection.execute(update_sql, update_data)
        self.connection.commit()

    def delete_blueprint_module(self, path: str) -> None:
        """Delete an existing module.

        Args:
            path (str): Full Python path to the module

        Raises:
            BlueprintModuleNotFound: Raised when the path does not exist.
        """
        blueprint_module_id = self._get_blueprint_module_id(path=path)
        delete_sql = 'DELETE FROM StackzillaBlueprintModule WHERE id=:id'
        self.connection.execute(delete_sql, {'id': blueprint_module_id})
        self.connection.commit()


    def delete_all_blueprint_modules(self) -> None:
        """Delete all of the blueprints from the database."""
        delete_sql = 'DELETE FROM StackzillaBlueprintModule'
        self.connection.execute(delete_sql)
        self.connection.commit()

    def create_blueprint_package(self, path: str) -> None:
        """Create a new blueprint package.

        Args:
            path (str): Full Python path of the package
        """
        try:
            self._get_blueprint_package_id(path=path)
            raise DuplicateBlueprintPackage
        except BlueprintPackageNotFound:
            pass

        sql = """INSERT INTO StackzillaBlueprintPackage ("path") VALUES (:path)"""
        insert_data = {
            'path': path,
        }

        try:
            self.connection.execute(sql, insert_data)
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            raise CreateBlueprintPackageFaiure() from exc

    def delete_blueprint_package(self, path: str) -> None:
        """Delete a blueprint package from the database.

        Args:
            path (str): Full Python path to the package
        """
        blueprint_package_id = self._get_blueprint_package_id(path=path)
        delete_sql = 'DELETE FROM StackzillaBlueprintPackage WHERE id=:id'
        self.connection.execute(delete_sql, {'id': blueprint_package_id})
        self.connection.commit()

    def delete_all_blueprint_packages(self) -> None:
        """Delete all of the blueprint packages from the database."""
        delete_sql = 'DELETE FROM StackzillaBlueprintPackage'
        self.connection.execute(delete_sql)
        self.connection.commit()

    def get_blueprint_package(self, path: str) -> bool:
        """Queries if a blueprint package exists in the database.

        Args:
            path (str): _description_

        Returns:
            bool: _description_
        """
        try:
            self._get_blueprint_package_id(path=path)
            return True
        except BlueprintPackageNotFound:
            return False

    def get_blueprint_packages(self) -> List[str]:
        """Fetch a list of all the blueprint packages.

        Returns:
            List[str]: A list of blueprint package names.
        """
        results: List[str] = []
        select_sql = 'SELECT * FROM StackzillaBlueprintPackage'
        cursor = self.connection.execute(select_sql)
        for row in cursor.fetchall():
            results.append(row['path'])

        return results

    def _value_encode(self, value: Any) -> str:
        """Pickle and base64 encode a value."""
        pickled_val = pickle.dumps(value)
        return base64.encodebytes(pickled_val).decode('ascii')

    def _value_decode(self, value: str) -> Any:
        """base64 decode and unpickle the value."""
        decoded_val = base64.decodebytes(value.encode("ascii"))
        return pickle.loads(decoded_val)

    def _get_blueprint_package_id(self, path: str) -> int:
        """Fetch the row ID for a given blueprint package, based on the provided path.

        Args:
            path (str): Full Python path to the blueprint package

        Raises:
            BlueprintPackageNotFound: Raised if the module is not found

        Returns:
            int: The row ID for the module
        """
        select_sql = 'SELECT * FROM StackzillaBlueprintPackage WHERE path=:path'
        cursor = self.connection.execute(select_sql, {'path': path})
        row = cursor.fetchone()
        if row is None:
            raise BlueprintPackageNotFound

        return row['id']

    def _get_blueprint_module_id(self, path: str) -> int:
        """Fetch the row ID for a given blueprint module, based on the provided path.

        Args:
            path (str): Full Python path to the blueprint module

        Raises:
            BlueprintModuleNotFound: Raised if the module is not found

        Returns:
            int: The row ID for the module
        """
        select_sql = 'SELECT * FROM StackzillaBlueprintModule WHERE path=:path'
        cursor = self.connection.execute(select_sql, {'path': path})
        row = cursor.fetchone()
        if row is None:
            raise BlueprintModuleNotFound

        return row['id']

    def _get_attribute_id(self, resource: StackzillaResource, name: str) -> int:
        """Fetch the database ID for the requested attribute.

        Args:
            resource (StackzillaResource): The resource that the attibute belongs to.
            name (str): Name of the attribute to fetch, as definined in the resource class

        Raises:
            AttributeNotFound: Raised if the attribute is not found

        Returns:
            int: Database ID of the StackzillaResource row
        """
        resource_id = self._resource_id_from_path(path=resource.path())

        select_sql = 'SELECT * FROM StackzillaAttribute WHERE resource_id=:resource_id AND name=:name'
        select_args = {'resource_id': resource_id, 'name': name}
        cursor = self.connection.execute(select_sql, select_args )

        row = cursor.fetchone()
        if row is None:
            raise AttributeNotFound

        return row['id']

    def _resource_id_from_path(self, path: str) -> int:
        """Helper method to fetch the ID of the resource by its Python path.

        Args:
            path (str): Python path of the resource within the blueprint

        Raises:
            ResourceNotFound: Raised if the path is not found

        Returns:
            int: The SQLite ID of the row for the resource
        """
        with self.connection:
            cursor = self.connection.execute('SELECT * FROM StackzillaResource WHERE path=:path', {'path': path})
            row = cursor.fetchone()
            if row is None:
                raise ResourceNotFound(path)

            return row['id']

    def _resource_from_path(self, path: str) -> dict:
        """Helper method to fetch an entire resource row from a given path.

        Args:
            path (str): The path to query

        Raises:
            ResourceNotFound: Raised if the resource is not found.

        Returns:
            dict: The row data for the match
        """
        with self.connection:
            cursor = self.connection.execute('SELECT * FROM StackzillaResource WHERE path=:path', {'path': path})
            row = cursor.fetchone()
            if row is None:
                raise ResourceNotFound(path)

            return row
