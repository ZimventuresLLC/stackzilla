"""Basic tests for the events framework."""
import gc
import typing
from contextlib import contextmanager
from typing import Dict

import pytest

from stackzilla.events import StackzillaEvent
from stackzilla.events.exceptions import (HandlerException, HandlerNotFound, ParameterMissing,
                                          UnsupportedHandlerType)
from stackzilla.resource import StackzillaResource

if typing.TYPE_CHECKING:
    from stackzilla.resource import StackzillaResource

@contextmanager
def garbage_cleanup(*args, **kwds):
    try:
        yield
    finally:
        gc.collect()

class MockResource:
    global_call_count = 0
    # Dictionary mapping of created resources and their handler call count
    was_called: Dict[int, int] = {}

    def __init__(self) -> None:
        self.call_count = 0
        MockResource.was_called[id(self)] = 0

    def handler(self, sender: 'StackzillaResource'):
        self.call_count += 1
        MockResource.global_call_count += 1
        MockResource.was_called[id(self)] += 1

    def handler_with_exception(self, sender):
        raise RuntimeError('Oh noes!')

    def handler_no_sender(self):
        """Intentioanlly missing the 'sender' parameter"""
        pass

    @staticmethod
    def verify_called():
        for id, count in MockResource.was_called.items():
            assert count > 0

class DummyResource(StackzillaResource):
    """A dummy resource to use as an event source."""

def test_basic_event():
    """Basic event subscription"""
    event = StackzillaEvent()
    resource = MockResource()

    event.attach(handler=resource.handler)

    event.invoke(sender=None)

    MockResource.verify_called()
    assert MockResource.global_call_count == 1

def test_resource_delete():
    """Test the scenario where a resource is delted without detaching itself from an event."""
    event = StackzillaEvent()
    MockResource.global_call_count = 0

    with garbage_cleanup():
        resource = MockResource()
        event.attach(handler=resource.handler)
        del resource

    event.invoke(sender=None)

    assert MockResource.global_call_count == 0

def test_multiple_attachments():
    """Attach multiple handlers to a single event."""
    event = StackzillaEvent()
    MockResource.global_call_count = 0
    resourceA = MockResource()
    resourceB = MockResource()
    resourceC = MockResource()
    for resource in [resourceA, resourceB, resourceC]:
        event.attach(resource.handler)

    event.invoke(sender=None)
    assert MockResource.global_call_count == 3

def test_multiple_attachments_with_deletion():
    """Attach multiple handlers to an event, but delete some!"""
    event = StackzillaEvent()
    MockResource.global_call_count = 0
    resourceA = MockResource()
    resourceB = MockResource()
    resourceC = MockResource()
    for resource in [resourceA, resourceB, resourceC]:
        event.attach(resource.handler)

    event.invoke(sender=None)
    assert MockResource.global_call_count == 3

    # Now, let's delete two of the handlers
    del resourceA
    del resourceB
    gc.collect()

    event.invoke(sender=None)
    assert MockResource.global_call_count == 4

def test_lambda_handlers():
    """Make sure that lambdas can be used as handlers."""
    event = StackzillaEvent()
    handler = lambda sender: print('yo')
    event.attach(handler=handler)
    event.invoke(sender=None)

def test_event_source():
    """Make sure that the event source makes it to the handler."""
    event = StackzillaEvent()
    def handler(sender):
        assert isinstance(sender, StackzillaResource)
    event.attach(handler=handler)
    sender = DummyResource()
    event.invoke(sender=sender)

def test_unsupported_handlers():
    """Verify that non-method/function handlers are rejected."""
    event = StackzillaEvent()

    with pytest.raises(UnsupportedHandlerType):
        string = 'foo'
        event.attach(handler=string)

    with pytest.raises(UnsupportedHandlerType):
        integer = 42
        event.attach(handler=integer)

    with pytest.raises(UnsupportedHandlerType):
        class Foo: pass
        event.attach(handler=Foo)

    with pytest.raises(UnsupportedHandlerType):
        class Bar: pass
        obj = Bar()
        event.attach(handler=obj)

def test_detach():
    event = StackzillaEvent()
    MockResource.global_call_count = 0
    resourceA = MockResource()
    resourceB = MockResource()
    resourceC = MockResource()
    for resource in [resourceA, resourceB, resourceC]:
        event.attach(resource.handler)

    event.invoke(sender=None)
    assert MockResource.global_call_count == 3

    # Now detach the first two
    event.detatch(resourceA.handler)
    event.detatch(resourceB.handler)

    event.invoke(sender=None)
    assert MockResource.global_call_count == 4

def test_invalid_detach():
    """Attempt to detach a handler that wasn't already attached."""
    event = StackzillaEvent()
    MockResource.global_call_count = 0
    resourceA = MockResource()
    event.attach(resourceA.handler)

    event.detatch(resourceA.handler)

    # Ensure the handler is no longer attached.
    with pytest.raises(HandlerNotFound):
        event.detatch(resourceA.handler)

def test_handler_exception():
    """Make sure that a handler which raises an exception doesn't screw everything up."""
    event = StackzillaEvent()
    resourceA = MockResource()
    event.attach(resourceA.handler_with_exception)

    with pytest.raises(HandlerException):
        event.invoke(sender=None)

def test_handler_missing_sender():
    """Pass in a handler that does not have all required arguments."""
    event = StackzillaEvent()
    resourceA = MockResource()
    event.attach(resourceA.handler_no_sender)

    with pytest.raises(ParameterMissing):
        event.invoke(sender=None)
