"""Verify the SQLite facility for resources."""
import pytest
from stackbot.database.exceptions import AttributeNotFound, DuplicateAttribute, ResourceNotFound
from stackbot.database.sqlite import StackBotSQLiteDB
from stackbot.resource.base import StackBotResource
from stackbot.attribute import StackBotAttribute

class Resource(StackBotResource):
    """Demo resource."""
    required = StackBotAttribute(required=True)
    default_int = StackBotAttribute(required=False, default=42)

class OtherResource(StackBotResource):
    """Demo Resource."""
    required = StackBotAttribute(required=True)

class MyResource(Resource):
    def __init__(self) -> None:
        super().__init__()
        self.required = "StackBot"
        self.default_int = 88

class MyOtherResource(Resource):
    def __init__(self) -> None:
        super().__init__()
        self.required = "Second StackBot"

def test_create_resource(database: StackBotSQLiteDB):
    """Ensure a resource can be created with its parameters."""

    my_resource = MyResource()
    my_other_resource = MyOtherResource()

    database.create_resource(resource=my_resource)
    for name in my_resource.attributes.keys():
        database.create_attribute(resource=my_resource, name=name, value=getattr(my_resource, name))

    db_resource = database.get_resource(path='stackbot.database.tests.test_resource.MyResource')
    assert db_resource.__class__ == MyResource

    # Get all of the attributes from the database and set them on the fetched resource
    for attr_name in db_resource.attributes.keys():
        value = database.get_attribute(resource=db_resource, name=attr_name)
        setattr(db_resource, attr_name, value)

    # Verify the database version
    assert db_resource.required == my_resource.required
    assert db_resource.default_int == my_resource.default_int

    # Ensure that a second object's values are unmodified
    assert my_other_resource.required == 'Second StackBot'
    assert my_other_resource.default_int == 42

    # Just for giggles, modify the database objects and ensure that the original stayed the same
    db_resource.default_int = 69
    assert my_resource.default_int == 88
    assert MyOtherResource().default_int == 42

def test_invalid_get_resource(database: StackBotSQLiteDB):
    """Test that invalid resoure queries raise the expected exception."""
    with pytest.raises(ResourceNotFound):
        database.get_resource(path='stackbot.database.tests.test_resource.MyResource')

    with pytest.raises(ResourceNotFound):
        database.get_resource(path='.junk')

    with pytest.raises(ResourceNotFound):
        database.get_resource(path=None)

def test_get_all_resources(database: StackBotSQLiteDB):
    """Verify the get_all_resources() method"""
    database.create_resource(resource=Resource)
    database.create_resource(resource=OtherResource)

    resources = database.get_all_resources()

    # Make sure that the resorce class type is correct
    for resource in resources:
        assert resource.__class__ in [Resource, OtherResource]

################################################################################
#  Attribute Test Cases
################################################################################
def test_duplicate_attributes(database: StackBotSQLiteDB):
    """Verify that you can't create the same attribute twice."""
    my_resource = MyResource()
    database.create_resource(resource=my_resource)

    # Snag a random attribute to persist to the database
    database.create_attribute(resource=my_resource, name='default_int', value=getattr(my_resource, 'default_int'))

    with pytest.raises(DuplicateAttribute):
        database.create_attribute(resource=my_resource, name='default_int', value=getattr(my_resource, 'default_int'))

def test_invalid_delete_attribute(database: StackBotSQLiteDB):
    """When deleting, make sure the correct exception is raised for attributes not in the database."""
    my_resource = MyResource()
    database.create_resource(resource=my_resource)

    # Attempt to delelte
    with pytest.raises(AttributeNotFound):
        database.delete_attribute(resource=my_resource, name='junk_attr')

def test_invalid_update_attribute(database: StackBotSQLiteDB):
    """When updating, make sure the correct exception is raised for attributes not in the database."""

    my_resource = MyResource()
    database.create_resource(resource=my_resource)

    # Attempt to update
    with pytest.raises(AttributeNotFound):
        database.update_attribute(resource=my_resource, name='junk_attr', value=123)

def test_update_attribute(database: StackBotSQLiteDB):
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
