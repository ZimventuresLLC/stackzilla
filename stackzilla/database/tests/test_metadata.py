"""Testing for the SQLite database implementation."""
import pytest

from stackzilla.database.exceptions import MetadataKeyNotFound
from stackzilla.database.sqlite import StackzillaSQLiteDB


def test_metadata(database: StackzillaSQLiteDB):
    """Validate basic metadata operations"""

    database.set_metadata(key='foo', value='bar')
    assert database.get_metadata(key='foo') == 'bar'

def test_missing_key(database: StackzillaSQLiteDB):
    """Verify missing keys raise the correct exception."""

    with pytest.raises(MetadataKeyNotFound):
        database.get_metadata(key='foo')

def test_key_deletion(database: StackzillaSQLiteDB):
    """Delete a metadata key."""
    database.set_metadata(key='foo', value='bar')
    database.delete_metadata(key='foo')

def test_invalid_key_deletion(database: StackzillaSQLiteDB):
    """Attempt to delete a metadata key that doesn't exist."""

    with pytest.raises(MetadataKeyNotFound):
        database.delete_metadata(key='foo')

def test_integer(database: StackzillaSQLiteDB):
    """Validate integer read/writes work."""
    database.set_metadata(key='foo', value=123)
    assert database.get_metadata(key='foo') == 123

def test_float(database: StackzillaSQLiteDB):
    """Validate floating point read/writes work."""
    database.set_metadata(key='foo', value=123.123)
    assert database.get_metadata(key='foo') == 123.123

def test_dict(database: StackzillaSQLiteDB):
    """Validate dictionary read/writes work."""
    value = {
        'int': 123,
        'float': 123.123,
        'dict': {'a': 1, 'b': 2},
    }

    database.set_metadata(key='foo', value=value)

    assert database.get_metadata(key='foo') == value
