"""Callback functions invoked by Click options."""
from stackbot.database.base import StackBotDBBase
from stackbot.database.sqlite import StackBotSQLiteDB


def namespace_callback(ctx, param, value):
    """Set the database provider used. Called anytime the --namespace parameter is required."""
    # Set the provider to use
    StackBotDBBase.provider = StackBotSQLiteDB

    return value