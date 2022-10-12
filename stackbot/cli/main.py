"""Main entrypoint for the application."""
import click
from colorama import init as colorama_init

from stackbot.cli.blueprint import blueprint
from stackbot.cli.metadata import metadata
from stackbot.cli.options import namespace_option
from stackbot.database.base import StackBotDB
from stackbot.database.exceptions import DatabaseExists
from stackbot.logging.utils import setup_logging


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
        StackBotDB.db.create()
    except DatabaseExists as exc:
        raise click.ClickException('database already exists') from exc


@cli.command(name='delete')
def delete():
    """Delete an existing namespace."""
    StackBotDB.db.delete()


# Add all of the sub-commands
cli.add_command(blueprint)
cli.add_command(metadata)
