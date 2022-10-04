"""Tests for the sqlite blueprint module database adapter."""
import pytest
from stackbot.database.exceptions import BlueprintModuleNotFound, DuplicateBlueprintModule
from stackbot.database.sqlite import StackBotSQLiteDB

fake_blueprint_data = """
from stackbot.provider.test.volume import Volume
class MyVolume(Volume):
    def __init__(self):
        self.size = 512
"""

def test_blueprint_module_create(database: StackBotSQLiteDB):
    """Verify basic module creation."""
    database.create_blueprint_module(path='storage.website', data=fake_blueprint_data)

    data = database.get_blueprint_module(path='storage.website')
    assert data == fake_blueprint_data

def test_duplicate_blueprint_module_create(database: StackBotSQLiteDB):
    """Verify duplicate module creates fail."""

    database.create_blueprint_module(path='storage.website', data=fake_blueprint_data)

    with pytest.raises(DuplicateBlueprintModule):
        database.create_blueprint_module(path='storage.website', data=fake_blueprint_data)

def test_blueprint_module_invalid_get(database: StackBotSQLiteDB):
    """Make sure the correct exception is raised for a non-existant path."""

    with pytest.raises(BlueprintModuleNotFound):
        database.get_blueprint_module(path='storage.website')

    with pytest.raises(BlueprintModuleNotFound):
        database.delete_blueprint_module(path='storage.webserver')

    with pytest.raises(BlueprintModuleNotFound):
        database.update_blueprint_module(path='storage.webserver', data=None)

def test_blueprint_module_delete(database: StackBotSQLiteDB):
    """Verify deletion works as expected."""

    # Create a blueprint module
    database.create_blueprint_module(path='storage.website', data=fake_blueprint_data)

    # Delete the module
    database.delete_blueprint_module(path='storage.website')

    # Verify the module was deleted by attempting to delete it again
    with pytest.raises(BlueprintModuleNotFound):
        database.delete_blueprint_module(path='storage.webserver')

def test_blueprint_module_delete_all(database: StackBotSQLiteDB):

    # Should work even though nothing is in there
    database.delete_all_blueprint_modules()

    # Add 3 modules
    module_names = ['alpha', 'beta', 'gamma']
    for module in module_names:
        database.create_blueprint_module(path=module, data=None)

    assert len(database.get_blueprint_modules()) == 3

    database.delete_all_blueprint_modules()

    assert len(database.get_blueprint_modules()) == 0

def test_blueprint_module_update(database: StackBotSQLiteDB):
    """Verify updating module data."""
    # Create a blueprint module
    database.create_blueprint_module(path='storage.website', data=fake_blueprint_data)

    data = database.get_blueprint_module(path='storage.website')
    assert data == fake_blueprint_data

    database.update_blueprint_module(path='storage.website', data='123')
    data = database.get_blueprint_module(path='storage.website')
    assert data == '123'

    database.update_blueprint_module(path='storage.website', data=None)
    data = database.get_blueprint_module(path='storage.website')
    assert data is None

def test_blueprint_get_modules(database: StackBotSQLiteDB):
    """Make sure that the get_blueprint_modules() works as expected"""
    module_names = ['alpha', 'beta', 'gamma', 'omega']

    # Verify there is nothing in the database as of yet
    assert database.get_blueprint_modules() == []

    # Add all of the modules to the database
    for module in module_names:
        database.create_blueprint_module(path=module, data=fake_blueprint_data)

    db_modules = database.get_blueprint_modules()

    # Verify that all of the modules are present
    for module in db_modules:
        assert module in module_names

    # Quick check to make sure the lists are the same size
    assert len(module_names) == len(db_modules)
