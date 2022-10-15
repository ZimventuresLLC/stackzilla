"""Tests for the sqlite blueprint module database adapter."""
import pytest

from stackzilla.database.exceptions import (BlueprintModuleNotFound,
                                            DuplicateBlueprintModule)
from stackzilla.database.sqlite import StackzillaSQLiteDB

FAKE_BLUEPRINT_DATA = """
from stackzilla.provider.test.volume import Volume
class MyVolume(Volume):
    def __init__(self):
        self.size = 512
"""

def test_blueprint_module_create(database: StackzillaSQLiteDB):
    """Verify basic module creation."""
    database.create_blueprint_module(path='storage.website', data=FAKE_BLUEPRINT_DATA)

    data = database.get_blueprint_module(path='storage.website')
    assert data == FAKE_BLUEPRINT_DATA

def test_duplicate_blueprint_module_create(database: StackzillaSQLiteDB):
    """Verify duplicate module creates fail."""

    database.create_blueprint_module(path='storage.website', data=FAKE_BLUEPRINT_DATA)

    with pytest.raises(DuplicateBlueprintModule):
        database.create_blueprint_module(path='storage.website', data=FAKE_BLUEPRINT_DATA)

def test_blueprint_module_invalid_get(database: StackzillaSQLiteDB):
    """Make sure the correct exception is raised for a non-existant path."""

    with pytest.raises(BlueprintModuleNotFound):
        database.get_blueprint_module(path='storage.website')

    with pytest.raises(BlueprintModuleNotFound):
        database.delete_blueprint_module(path='storage.webserver')

    with pytest.raises(BlueprintModuleNotFound):
        database.update_blueprint_module(path='storage.webserver', data=None)

def test_blueprint_module_delete(database: StackzillaSQLiteDB):
    """Verify deletion works as expected."""

    # Create a blueprint module
    database.create_blueprint_module(path='storage.website', data=FAKE_BLUEPRINT_DATA)

    # Delete the module
    database.delete_blueprint_module(path='storage.website')

    # Verify the module was deleted by attempting to delete it again
    with pytest.raises(BlueprintModuleNotFound):
        database.delete_blueprint_module(path='storage.webserver')

def test_blueprint_module_delete_all(database: StackzillaSQLiteDB):
    """Verify that deleting all blueprint modules works."""
    # Should work even though nothing is in there
    database.delete_all_blueprint_modules()

    # Add 3 modules
    module_names = ['alpha', 'beta', 'gamma']
    for module in module_names:
        database.create_blueprint_module(path=module, data=None)

    assert len(database.get_blueprint_modules()) == 3

    database.delete_all_blueprint_modules()

    assert len(database.get_blueprint_modules()) == 0

def test_blueprint_module_update(database: StackzillaSQLiteDB):
    """Verify updating module data."""
    # Create a blueprint module
    database.create_blueprint_module(path='storage.website', data=FAKE_BLUEPRINT_DATA)

    data = database.get_blueprint_module(path='storage.website')
    assert data == FAKE_BLUEPRINT_DATA

    database.update_blueprint_module(path='storage.website', data='123')
    data = database.get_blueprint_module(path='storage.website')
    assert data == '123'

    database.update_blueprint_module(path='storage.website', data=None)
    data = database.get_blueprint_module(path='storage.website')
    assert data is None

def test_blueprint_get_modules(database: StackzillaSQLiteDB):
    """Make sure that the get_blueprint_modules() works as expected"""
    module_names = ['alpha', 'beta', 'gamma', 'omega']

    # Verify there is nothing in the database as of yet
    assert database.get_blueprint_modules() == []

    # Add all of the modules to the database
    for module in module_names:
        database.create_blueprint_module(path=module, data=FAKE_BLUEPRINT_DATA)

    db_modules = database.get_blueprint_modules()

    # Verify that all of the modules are present
    for module in db_modules:
        assert module in module_names

    # Quick check to make sure the lists are the same size
    assert len(module_names) == len(db_modules)
