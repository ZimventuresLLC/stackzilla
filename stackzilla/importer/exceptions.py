"""Exceptions for the importer module."""

class ClassNotFound(Exception):
    """Raised when no results are found during a class search."""

class NotLoaded(Exception):
    """Raised if an operation is performed prior to the blueprint being loaded."""
