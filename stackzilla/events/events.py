"""Module for all of the Stackzilla event system logic."""
import inspect
import typing
import weakref
from typing import Callable, List

from stackzilla.events.exceptions import (HandlerException, HandlerNotFound,
                                          ParameterMissing,
                                          UnsupportedHandlerType)

if typing.TYPE_CHECKING:
    from stackzilla.resource import StackzillaResource

class StackzillaEvent:
    """The event class....duh."""

    def __init__(self) -> None:
        """Default constructor. Sets up an empty list of handlers."""
        self._handlers: List[weakref.WeakMethod] = []

    def attach(self, handler: Callable) -> None:
        """Attach a handler to this event.

        Args:
            handler (Callable): A method, function, or lambda that will be called when the event is triggered.

        Raises:
            UnsupportedHandlerType: Raised if an unsupported handler is passed in
        """
        # Do not support classes as handlers
        if inspect.isclass(handler):
            raise UnsupportedHandlerType('Classes are not supported as handler types.')

        if inspect.ismethod(handler):
            ref = weakref.WeakMethod(handler)
        elif callable(handler):
            ref = weakref.ref(handler)
        else:
            raise UnsupportedHandlerType(f'{type(handler)} is not supported')
        self._handlers.append(ref)

    def detatch(self, handler: Callable) -> None:
        """Detach a previously attached handler.

        Args:
            handler (Callable): The handler to detach.

        Raises:
            HandlerNotFound: Raised if the handler was not previously attached
        """
        for ref in self._handlers:
            if ref() == handler:
                self._handlers.remove(ref)
                return

        raise HandlerNotFound()

    def invoke(self, sender: 'StackzillaResource', **kwargs):
        """Invoke any handlers.

        Args:
            sender (StackzillaResource): The resource which is causing the event to be triggered.
        """
        for ref in self._handlers:

            # Test the weakref to ensure it isn't dead
            resolved_ref = ref()
            if resolved_ref:

                try:
                    resolved_ref(sender=sender, **kwargs)
                except TypeError as err:
                    if "got an unexpected keyword argument 'sender'" in str(err):
                        raise ParameterMissing('sender argument is missing from handler') from err
                except Exception as exc: # pylint: disable=broad-except
                    raise HandlerException(exc) from exc
            else:
                # The weakref is dead, remove this handler!
                self._handlers.remove(ref)
