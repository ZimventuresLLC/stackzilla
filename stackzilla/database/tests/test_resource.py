"""Verify the SQLite facility for resources."""
# pylint: disable=abstract-method
import pytest

from stackzilla.attribute import StackzillaAttribute
from stackzilla.database.exceptions import (AttributeNotFound,
                                            DuplicateAttribute,
                                            ResourceNotFound)
from stackzilla.database.sqlite import StackzillaSQLiteDB
from stackzilla.resource.base import ResourceVersion, StackzillaResource


class Resource(StackzillaResource):
    """Demo resource."""
    required = StackzillaAttribute(required=True)
    default_int = StackzillaAttribute(required=False, default=42)

    @classmethod
    def version(cls) -> ResourceVersion:
        return ResourceVersion(major=1, minor=0, build=0, name='FCS')

class OtherResource(StackzillaResource):
    """Demo Resource."""
    required = StackzillaAttribute(required=True)

    @classmethod
    def version(cls) -> ResourceVersion:
        return ResourceVersion(major=1, minor=0, build=0, name='FCS')

class MyResource(Resource):
    """Override the default int."""
    def __init__(self) -> None:
        super().__init__()
        self.required = "Stackzilla"
        self.default_int = 88

class MyOtherResource(Resource):
    """Override the default required string"""
    def __init__(self) -> None:
        super().__init__()
        self.required = "Second Stackzilla"

def test_create_resource(database: StackzillaSQLiteDB):
    """Ensure a resource can be created with its parameters."""

    my_resource = MyResource()
    my_other_resource = MyOtherResource()

    database.create_resource(resource=my_resource)
    for name in my_resource.attributes:
        database.create_attribute(resource=my_resource, name=name, value=getattr(my_resource, name))

    db_resource = database.get_resource(path='stackzilla.database.tests.test_resource.MyResource')
    assert db_resource.__class__ == MyResource
    assert db_resource.version() == MyResource.version()

    # Get all of the attributes from the database and set them on the fetched resource
    for attr_name in db_resource.attributes.keys():
        value = database.get_attribute(resource=db_resource, name=attr_name)
        setattr(db_resource, attr_name, value)

    # Verify the database version
    assert db_resource.required == my_resource.required
    assert db_resource.default_int == my_resource.default_int

    # Ensure that a second object's values are unmodified
    assert my_other_resource.required == 'Second Stackzilla'
    assert my_other_resource.default_int == 42

    # Just for giggles, modify the database objects and ensure that the original stayed the same
    db_resource.default_int = 69
    assert my_resource.default_int == 88
    assert MyOtherResource().default_int == 42

def test_invalid_get_resource(database: StackzillaSQLiteDB):
    """Test that invalid resoure queries raise the expected exception."""
    with pytest.raises(ResourceNotFound):
        database.get_resource(path='stackzilla.database.tests.test_resource.MyResource')

    with pytest.raises(ResourceNotFound):
        database.get_resource(path='.junk')

    with pytest.raises(ResourceNotFound):
        database.get_resource(path=None)

def test_get_all_resources(database: StackzillaSQLiteDB):
    """Verify the get_all_resources() method"""

    Resource().create_in_db()
    OtherResource().create_in_db()

    resources = database.get_all_resources()

    # Make sure that the resorce class type is correct
    for resource in resources:
        assert resource.__class__ in [Resource, OtherResource]

################################################################################
#  Attribute Test Cases
################################################################################
def test_duplicate_attributes(database: StackzillaSQLiteDB):
    """Verify that you can't create the same attribute twice."""
    my_resource = MyResource()
    my_resource.create_in_db()

    # Snag a random attribute to persist to the database
    with pytest.raises(DuplicateAttribute):
        database.create_attribute(resource=my_resource, name='default_int', value=getattr(my_resource, 'default_int'))

def test_invalid_delete_attribute(database: StackzillaSQLiteDB):
    """When deleting, make sure the correct exception is raised for attributes not in the database."""
    my_resource = MyResource()
    database.create_resource(resource=my_resource)

    # Attempt to delelte
    with pytest.raises(AttributeNotFound):
        database.delete_attribute(resource=my_resource, name='junk_attr')

def test_invalid_update_attribute(database: StackzillaSQLiteDB):
    """When updating, make sure the correct exception is raised for attributes not in the database."""

    my_resource = MyResource()
    database.create_resource(resource=my_resource)

    # Attempt to update
    with pytest.raises(AttributeNotFound):
        database.update_attribute(resource=my_resource, name='junk_attr', value=123)

def test_update_attribute(database: StackzillaSQLiteDB):
    """Ensure that updating attibutes in the database. works"""
    my_resource = MyResource()
    database.create_resource(resource=my_resource)

    # Create the resource in the database with its default value
    database.create_attribute(resource=my_resource, name='default_int', value=getattr(my_resource, 'default_int'))

    value = database.get_attribute(resource=my_resource, name='default_int')
    assert value == my_resource.default_int

    value += 100
    database.update_attribute(resource=my_resource, name='default_int', value=value)

    # Make sure that the updated value matches the original value + the modification
    updated_db_value = database.get_attribute(resource=my_resource, name='default_int')
    assert updated_db_value == my_resource.default_int + 100
