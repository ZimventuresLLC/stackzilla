"""Pytest configuration file for the database tests."""
import pytest

from stackzilla.database.base import StackzillaDB
from stackzilla.database.sqlite import StackzillaSQLiteDB


@pytest.fixture
def database():
    """Fixture that returns an in-memory database."""
    memory_db = StackzillaSQLiteDB(name='test')
    memory_db.create(in_memory=True)

    # Set this so that Stackzilla will use it for all DB operations
    StackzillaDB.db = memory_db

    return memory_db
