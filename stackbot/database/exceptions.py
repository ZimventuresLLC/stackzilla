"""Exceptions for the database module."""

class DatabaseExists(Exception):
    """Raised if the database already exists during a create operation."""

class DatabaseNotFound(Exception):
    """Raised for cases where the specified database name was not found."""

class DatabaseNotOpen(Exception):
    """Raised when the database is being accessed prior to being open."""
class MetadataKeyNotFound(Exception):
    """Raised when the metadata key is not found for a given query."""

class CreateResourceFailure(Exception):
    """Raised when the resource creation operation fails."""

class ResourceNotFound(Exception):
    """Raised when the requested resource is not found in the database."""

class AttributeNotFound(Exception):
    """Raised when the requested attribute is not found in the database."""

class DuplicateAttribute(Exception):
    """Raised when an attribute already exists in the database during a create event."""

class CreateAttributeFailure(Exception):
    """Raised when attribute creation fails."""

class BlueprintModuleNotFound(Exception):
    """Raised when the blueprint module isn't found during a search operation."""

class DuplicateBlueprintModule(Exception):
    """Raised when the user tries to create a blueprint module that already exists."""

class CreateBlueprintModuleFailure(Exception):
    """Raised when the blueprint module creation fails."""

class CreateBlueprintPackageFaiure(Exception):
    """Raised when the blueprint package creation fails."""
class BlueprintPackageNotFound(Exception):
    """Raised when the blueprint package is not found during a search operation."""

class DuplicateBlueprintPackage(Exception):
    """Raised when a package already exists during a create operation."""
