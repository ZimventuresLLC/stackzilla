"""Pytest configuration file for the importer tests."""
import pytest

from stackzilla.database.sqlite import StackzillaSQLiteDB


@pytest.fixture
def database():
    """Fixture that returns an in-memory database."""
    memory_db = StackzillaSQLiteDB(name='test')
    memory_db.create(in_memory=True)
    return memory_db
