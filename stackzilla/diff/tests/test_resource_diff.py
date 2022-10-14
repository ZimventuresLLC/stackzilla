"""Test for the resource diffing logic."""
# pylint: disable=abstract-method

from stackzilla.attribute import StackzillaAttribute
from stackzilla.diff import StackzillaDiff, StackzillaDiffResult
from stackzilla.resource import StackzillaResource


class BaseResource(StackzillaResource):
    """Base resource."""
    attr_int = StackzillaAttribute(required=True, default=42)
    attr_string = StackzillaAttribute(required=True, default="Stackzilla")

class BaseResoureModified(StackzillaResource):
    """A base resource that will be modified."""
    attr_int = StackzillaAttribute(required=True, default=88)
    attr_string = StackzillaAttribute(required=True, default="Stackzilla-New")

class BaseResourceNew(BaseResource):
    """A resource with a new attribute added."""
    attr_new_int = StackzillaAttribute(required=True, default=123)
    attr_new_string = StackzillaAttribute(required=True)

class SourceResource(BaseResource):
    """The "source" resource which acts like a disk blueprint resource."""

class DestinationResource(BaseResource):
    """The "dest" resource which acts like a database blueprint resource."""

class SourceResourceModified(BaseResoureModified):
    """A modified disk resource."""
class SourceResourceNew(BaseResourceNew):
    """A new disk resource."""

def test_resource_diff_same():
    """Ensure that two resources with identical attributes have no differences."""
    # Define the two objects
    diff = StackzillaDiff()
    src_obj = SourceResource()
    dest_obj = DestinationResource()

    # Perform the diff
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)
    assert result == StackzillaDiffResult.SAME
    assert len(diffs) == 0

def test_resource_src_diff_actual():
    """Detect differences in the source due to changes in the derrived class."""

    # Define the two objects
    diff = StackzillaDiff()
    src_obj = SourceResource()
    dest_obj = DestinationResource()

    src_obj.attr_int = 88

    diff = StackzillaDiff()

    (result, diffs)  = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackzillaDiffResult.CONFLICT
    assert 'attr_int' in diffs
    assert diffs['attr_int'].result == StackzillaDiffResult.CONFLICT
    assert diffs['attr_int'].src_value == 88
    assert diffs['attr_int'].dest_value == 42

def test_resource_dest_diff_actual():
    """Detect differences in the destination due to changes in the derrived class."""

    # Define the two objects
    diff = StackzillaDiff()
    src_obj = SourceResource()
    dest_obj = DestinationResource()

    dest_obj.attr_int = 88

    diff = StackzillaDiff()
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackzillaDiffResult.CONFLICT
    assert 'attr_int' in diffs
    assert diffs['attr_int'].result == StackzillaDiffResult.CONFLICT
    assert diffs['attr_int'].src_value == 42
    assert diffs['attr_int'].dest_value == 88

def test_resource_diff_default():
    """Make sure that if the default value changes on the base class, it's detected in the diff."""
    src_obj = SourceResourceModified()
    dest_obj = SourceResource()

    diff = StackzillaDiff()
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackzillaDiffResult.CONFLICT
    assert len(diffs) == 2
    assert 'attr_int' in diffs
    assert diffs['attr_int'].result == StackzillaDiffResult.CONFLICT
    assert diffs['attr_int'].src_value == 88
    assert diffs['attr_int'].dest_value == 42

    assert 'attr_string' in diffs
    assert diffs['attr_string'].result == StackzillaDiffResult.CONFLICT
    assert diffs['attr_string'].src_value == 'Stackzilla-New'
    assert diffs['attr_string'].dest_value == 'Stackzilla'

def test_resource_diff_new_source():
    """Make sure source resources with new attributes are detected"""
    src_obj = SourceResource()
    dest_obj = SourceResourceNew()

    diff = StackzillaDiff()
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackzillaDiffResult.CONFLICT
    assert len(diffs) == 2
    assert 'attr_new_int' in diffs
    assert 'attr_new_string' in diffs

    # The attributes are new, so they shouldn't be in the destination
    assert diffs['attr_new_int'].src_attribute is None
    assert diffs['attr_new_string'].src_attribute is None

def test_resource_diff_deleted_source():
    """Detect when a source resource does not have the same attributes as the destination."""

    dest_obj = SourceResource()
    src_obj = SourceResourceNew()

    diff = StackzillaDiff()
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackzillaDiffResult.CONFLICT
    assert len(diffs) == 2
    assert 'attr_new_int' in diffs
    assert 'attr_new_string' in diffs

    # The attributes are new, so they shouldn't be in the destination
    assert diffs['attr_new_int'].dest_attribute is None
    assert diffs['attr_new_string'].dest_attribute is None
