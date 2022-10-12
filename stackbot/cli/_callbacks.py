"""Callback functions invoked by Click options."""
from stackbot.database.sqlite import StackBotSQLiteDB


def namespace_callback(_ctx, _param, value):
    """Set the database provider used. Called anytime the --namespace parameter is required."""
    # Intantiate the database object, which sets itself to the StackBotDB.db singleton
    StackBotSQLiteDB(name=value)

    return value
