import pytest
from stackbot.database.sqlite import StackBotSQLiteDB

@pytest.fixture
def database():
    """Fixture that returns an in-memory database"""
    memory_db = StackBotSQLiteDB(name='test')
    memory_db.create(in_memory=True)
    return memory_db
