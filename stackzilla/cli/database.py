"""Module for database debugging CLI."""
import click

#from stackzilla.database.base import StackzillaDB
#from stackzilla.blueprint import StackzillaBlueprint
#from stackzilla.database.exceptions import ResourceNotFound

@click.group(name='database')
def database():
    """Command group for all database CLI commands."""
