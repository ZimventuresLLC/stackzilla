"""Click handlers for the metadata sub-command."""
import click

from stackbot.cli.options import key_option, value_option
from stackbot.database.base import StackBotDBBase
from stackbot.database.exceptions import MetadataKeyNotFound


@click.group(name='metadata')
def metadata():
    """Command group for all metadata CLI commands."""

@metadata.command('set')
@click.pass_context
@key_option
@value_option
def set_key(ctx, key, value):
    """Set the metadata value for the specified key."""
    database: StackBotDBBase = StackBotDBBase.provider(name=ctx.obj['namespace'])
    database.open()
    database.set_metadata(key=key, value=value)

@metadata.command('get')
@click.pass_context
@key_option
def get_key(ctx, key):
    """Query the value for the specified metadata entry."""
    database: StackBotDBBase = StackBotDBBase.provider(name=ctx.obj['namespace'])
    database.open()

    try:
        value = database.get_metadata(key=key)
    except MetadataKeyNotFound as exc:
        raise click.ClickException(f'key ({key}) not found') from exc

    click.echo(value)

@metadata.command('delete')
@click.pass_context
@key_option
def delete_key(ctx, key):
    """Delete the specified metadata entry."""
    database: StackBotDBBase = StackBotDBBase.provider(name=ctx.obj['namespace'])
    database.open()

    try:
        database.delete_metadata(key=key)
    except MetadataKeyNotFound as exc:
        raise click.ClickException(f'key ({key}) not found') from exc

@metadata.command('exists')
@click.pass_context
@key_option
def exists(ctx, key):
    """Test if a metadata key exists. Prints "true" or "false"."""
    database: StackBotDBBase = StackBotDBBase.provider(name=ctx.obj['namespace'])
    database.open()

    if database.check_metadata(key=key):
        click.echo('true')
    else:
        click.echo('false')
