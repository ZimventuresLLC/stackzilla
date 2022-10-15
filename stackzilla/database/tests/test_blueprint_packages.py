"""Tests for the sqlite blueprint package database adapter."""
import pytest

from stackzilla.database.exceptions import (BlueprintPackageNotFound,
                                            DuplicateBlueprintPackage)
from stackzilla.database.sqlite import StackzillaSQLiteDB


def test_blueprint_package_create(database: StackzillaSQLiteDB):
    """Verify basic package creation."""
    database.create_blueprint_package(path='storage.website')

    assert database.get_blueprint_package(path='storage.website') is True

def test_duplicate_blueprint_package_create(database: StackzillaSQLiteDB):
    """Verify duplicate package creates fail."""

    database.create_blueprint_package(path='storage.website')

    with pytest.raises(DuplicateBlueprintPackage):
        database.create_blueprint_package(path='storage.website')

def test_blueprint_package_invalid_get(database: StackzillaSQLiteDB):
    """Make sure the correct exception is raised for a non-existant path."""

    assert database.get_blueprint_package(path='storage.website') is False

    with pytest.raises(BlueprintPackageNotFound):
        database.delete_blueprint_package(path='storage.webserver')

def test_blueprint_package_delete(database: StackzillaSQLiteDB):
    """Verify deletion works as expected."""

    # Create a blueprint package
    database.create_blueprint_package(path='storage.website')

    # Delete the package
    database.delete_blueprint_package(path='storage.website')

    # Verify the package was deleted by attempting to delete it again
    with pytest.raises(BlueprintPackageNotFound):
        database.delete_blueprint_package(path='storage.webserver')

def test_blueprint_package_delete_all(database: StackzillaSQLiteDB):
    """Verify that deleting all packages works."""
    # Should work even though nothing is in there
    database.delete_all_blueprint_packages()

    # Add 3 packages
    module_names = ['alpha', 'beta', 'gamma']
    for module in module_names:
        database.create_blueprint_package(path=module)

    assert len(database.get_blueprint_packages()) == 3

    database.delete_all_blueprint_packages()

    assert len(database.get_blueprint_packages()) == 0

def test_blueprint_get_packages(database: StackzillaSQLiteDB):
    """Make sure that the get_blueprint_packages() works as expected"""
    package_names = ['alpha', 'beta', 'gamma', 'omega']

    # Verify there is nothing in the database as of yet
    assert database.get_blueprint_packages() == []

    # Add all of the packages to the database
    for package in package_names:
        database.create_blueprint_package(path=package)

    db_packages = database.get_blueprint_packages()

    # Verify that all of the packages are present
    for package in db_packages:
        assert package in package_names

    # Quick check to make sure the lists are the same size
    assert len(package_names) == len(db_packages)
