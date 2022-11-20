"""Exceptions for the Stackzilla events module."""

class UnsupportedHandlerType(Exception):
    """Raised if the user tries to register a non-method/function as a handler."""

class HandlerNotFound(Exception):
    """Raised when the specified handler is not found during a detachment request. """
