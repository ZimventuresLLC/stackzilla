"""Module for database debugging CLI."""
import pprint

import click

from stackzilla.blueprint import StackzillaBlueprint
from stackzilla.database.base import StackzillaDB
from stackzilla.database.exceptions import ResourceNotFound
from stackzilla.resource.base import StackzillaResource
from stackzilla.utils.constants import DISK_BP_PREFIX

from .options import path_option


@click.group(name='database')
def database():
    """Command group for all database CLI commands."""

@database.command('show-resource')
@path_option
def show_resource(path):
    """Show a resource, and its attributes, as it is in the database."""
    StackzillaDB.db.open()

    # Import the blueprint from disk
    db_blueprint = StackzillaBlueprint(python_root=DISK_BP_PREFIX)
    db_blueprint.load()

    # Load the resource specified by path
    try:
        resource: StackzillaResource = db_blueprint.get_resource(path=path)
        resource = resource()
        resource.load_from_db()
    except ResourceNotFound as exc:
        raise click.ClickException('Resource specified by path not found') from exc

    pprint.pprint(resource.__dict__)
