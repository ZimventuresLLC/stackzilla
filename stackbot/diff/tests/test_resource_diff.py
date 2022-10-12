"""Test for the resource diffing logic."""
# pylint: disable=abstract-method

from stackbot.attribute import StackBotAttribute
from stackbot.diff import StackBotDiff, StackBotDiffResult
from stackbot.resource import StackBotResource


class BaseResource(StackBotResource):
    """Base resource."""
    attr_int = StackBotAttribute(required=True, default=42)
    attr_string = StackBotAttribute(required=True, default="StackBot")

class BaseResoureModified(StackBotResource):
    """A base resource that will be modified."""
    attr_int = StackBotAttribute(required=True, default=88)
    attr_string = StackBotAttribute(required=True, default="StackBot-New")

class BaseResourceNew(BaseResource):
    """A resource with a new attribute added."""
    attr_new_int = StackBotAttribute(required=True, default=123)
    attr_new_string = StackBotAttribute(required=True)

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
    diff = StackBotDiff()
    src_obj = SourceResource()
    dest_obj = DestinationResource()

    # Perform the diff
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)
    assert result == StackBotDiffResult.SAME
    assert len(diffs) == 0

def test_resource_src_diff_actual():
    """Detect differences in the source due to changes in the derrived class."""

    # Define the two objects
    diff = StackBotDiff()
    src_obj = SourceResource()
    dest_obj = DestinationResource()

    src_obj.attr_int = 88

    diff = StackBotDiff()

    (result, diffs)  = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackBotDiffResult.CONFLICT
    assert 'attr_int' in diffs
    assert diffs['attr_int'].result == StackBotDiffResult.CONFLICT
    assert diffs['attr_int'].src_value == 88
    assert diffs['attr_int'].dest_value == 42

def test_resource_dest_diff_actual():
    """Detect differences in the destination due to changes in the derrived class."""

    # Define the two objects
    diff = StackBotDiff()
    src_obj = SourceResource()
    dest_obj = DestinationResource()

    dest_obj.attr_int = 88

    diff = StackBotDiff()
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackBotDiffResult.CONFLICT
    assert 'attr_int' in diffs
    assert diffs['attr_int'].result == StackBotDiffResult.CONFLICT
    assert diffs['attr_int'].src_value == 42
    assert diffs['attr_int'].dest_value == 88

def test_resource_diff_default():
    """Make sure that if the default value changes on the base class, it's detected in the diff."""
    src_obj = SourceResourceModified()
    dest_obj = SourceResource()

    diff = StackBotDiff()
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackBotDiffResult.CONFLICT
    assert len(diffs) == 2
    assert 'attr_int' in diffs
    assert diffs['attr_int'].result == StackBotDiffResult.CONFLICT
    assert diffs['attr_int'].src_value == 88
    assert diffs['attr_int'].dest_value == 42

    assert 'attr_string' in diffs
    assert diffs['attr_string'].result == StackBotDiffResult.CONFLICT
    assert diffs['attr_string'].src_value == 'StackBot-New'
    assert diffs['attr_string'].dest_value == 'StackBot'

def test_resource_diff_new_source():
    """Make sure source resources with new attributes are detected"""
    src_obj = SourceResource()
    dest_obj = SourceResourceNew()

    diff = StackBotDiff()
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackBotDiffResult.CONFLICT
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

    diff = StackBotDiff()
    (result, diffs) = diff.compare(source=src_obj, destination=dest_obj)

    assert result == StackBotDiffResult.CONFLICT
    assert len(diffs) == 2
    assert 'attr_new_int' in diffs
    assert 'attr_new_string' in diffs

    # The attributes are new, so they shouldn't be in the destination
    assert diffs['attr_new_int'].dest_attribute is None
    assert diffs['attr_new_string'].dest_attribute is None
