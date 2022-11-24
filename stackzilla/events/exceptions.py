"""Exceptions for the Stackzilla events module."""

class UnsupportedHandlerType(Exception):
    """Raised if the user tries to register a non-method/function as a handler."""

class HandlerNotFound(Exception):
    """Raised when the specified handler is not found during a detachment request."""

class ParameterMissing(Exception):
    """Raised when a required parameter is missing from a handler."""

class HandlerException(Exception):
    """Raised when any handler throws an exception."""
