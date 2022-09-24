"""Main entrypoint for the application."""
import click

from stackbot.blueprint.importer import Importer
from stackbot.cli.metadata import metadata
from stackbot.cli.options import namespace_option
from stackbot.database.base import StackBotDBBase
from stackbot.database.exceptions import DatabaseExists
from stackbot.logging.utils import setup_logging


@click.group(name='cli')
@namespace_option
@click.pass_context
def cli(ctx, namespace):
    """Main entrypoint to all cli commands."""
    setup_logging()

    ctx.ensure_object(dict)

    # Pass on the namespace name to all commands
    ctx.obj['namespace'] = namespace


@cli.command(name='init')
@click.pass_context
def init(ctx):
    """Initialize a new namespace."""
    database = StackBotDBBase.provider(name=ctx.obj['namespace'])

    try:
        database.create()
    except DatabaseExists as exc:
        raise click.ClickException('database already exists') from exc


@cli.command(name='delete')
@click.pass_context
def delete(ctx):
    """Delete an existing namespace."""
    database = StackBotDBBase.provider(name=ctx.obj['namespace'])
    database.delete()

# Add all of the sub-commands
cli.add_command(metadata)
