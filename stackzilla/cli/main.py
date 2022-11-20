"""Main entrypoint for the application."""
import click
from colorama import init as colorama_init

from stackzilla.cli.blueprint import blueprint
from stackzilla.cli.compute import compute
from stackzilla.cli.database import database
from stackzilla.cli.kubernetes import kubernetes
from stackzilla.cli.metadata import metadata
from stackzilla.cli.options import namespace_option
from stackzilla.cli.resource import resource
from stackzilla.database.base import StackzillaDB
from stackzilla.database.exceptions import DatabaseExists
from stackzilla.logger.utils import setup_logging


@click.group(name='cli')
@namespace_option
@click.pass_context
def cli(ctx, namespace):
    """Main entrypoint to all cli commands."""
    setup_logging()

    # Needs to be called for initialization on Windows platforms
    colorama_init()

    ctx.ensure_object(dict)

    # Pass on the namespace name to all commands
    ctx.obj['namespace'] = namespace


@cli.command(name='init')
def init():
    """Initialize a new namespace."""
    try:
        StackzillaDB.db.create()
    except DatabaseExists as exc:
        raise click.ClickException('database already exists') from exc


@cli.command(name='delete')
def delete():
    """Delete an existing namespace."""
    if click.confirm('Are you sure? This will erase the database WITHOUT cleaning up any resources.'):
        StackzillaDB.db.delete()


# Add all of the sub-commands
cli.add_command(blueprint)
cli.add_command(compute)
cli.add_command(database)
cli.add_command(kubernetes)
cli.add_command(metadata)
cli.add_command(resource)
