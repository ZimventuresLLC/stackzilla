"""Exceptions for the database module."""

class DatabaseExists(Exception):
    """Raised if the database already exists during a create operation."""

class DatabaseNotFound(Exception):
    """Raised for cases where the specified database name was not found."""

class MetadataKeyNotFound(Exception):
    """Raised when the metadata key is not found for a given query."""
