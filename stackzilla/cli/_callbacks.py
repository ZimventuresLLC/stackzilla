"""Callback functions invoked by Click options."""
from stackzilla.database.sqlite import StackzillaSQLiteDB


def namespace_callback(_ctx, _param, value):
    """Set the database provider used. Called anytime the --namespace parameter is required."""
    # Intantiate the database object, which sets itself to the StackzillaDB.db singleton
    StackzillaSQLiteDB(name=value)

    return value
