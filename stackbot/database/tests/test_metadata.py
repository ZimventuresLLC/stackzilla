"""Testing for the SQLite database implementation."""
import pytest

from stackbot.database.sqlite import StackBotSQLiteDB
from stackbot.database.exceptions import MetadataKeyNotFound

def test_metadata(database: StackBotSQLiteDB):
    """Validate basic metadata operations"""

    database.set_metadata(key='foo', value='bar')
    assert database.get_metadata(key='foo') == 'bar'

def test_missing_key(database: StackBotSQLiteDB):
    """Verify missing keys raise the correct exception."""

    with pytest.raises(MetadataKeyNotFound):
        database.get_metadata(key='foo')

def test_key_deletion(database: StackBotSQLiteDB):
    """Delete a metadata key."""
    database.set_metadata(key='foo', value='bar')
    database.delete_metadata(key='foo')

def test_invalid_key_deletion(database: StackBotSQLiteDB):
    """Attempt to delete a metadata key that doesn't exist."""

    with pytest.raises(MetadataKeyNotFound):
        database.delete_metadata(key='foo')

def test_integer(database: StackBotSQLiteDB):
    """Validate integer read/writes work."""
    database.set_metadata(key='foo', value=123)
    assert database.get_metadata(key='foo') == 123

def test_float(database: StackBotSQLiteDB):
    """Validate floating point read/writes work."""
    database.set_metadata(key='foo', value=123.123)
    assert database.get_metadata(key='foo') == 123.123

def test_dict(database: StackBotSQLiteDB):
    """Validate dictionary read/writes work."""
    value = {
        'int': 123,
        'float': 123.123,
        'dict': {'a': 1, 'b': 2},
    }

    database.set_metadata(key='foo', value=value)

    assert database.get_metadata(key='foo') == value
