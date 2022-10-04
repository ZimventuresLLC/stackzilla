"""Click handlers for the metadata sub-command."""
import click

from stackbot.cli.options import key_option, value_option
from stackbot.database.base import StackBotDB
from stackbot.database.exceptions import MetadataKeyNotFound


@click.group(name='metadata')
def metadata():
    """Command group for all metadata CLI commands."""

@metadata.command('set')
@key_option
@value_option
def set_key(key, value):
    """Set the metadata value for the specified key."""
    StackBotDB.db.open()
    StackBotDB.db.set_metadata(key=key, value=value)

@metadata.command('get')
@key_option
def get_key(key):
    """Query the value for the specified metadata entry."""
    StackBotDB.db.open()

    try:
        value = StackBotDB.db.get_metadata(key=key)
    except MetadataKeyNotFound as exc:
        raise click.ClickException(f'key ({key}) not found') from exc

    click.echo(value)

@metadata.command('delete')
@key_option
def delete_key(key):
    """Delete the specified metadata entry."""
    StackBotDB.db.open()

    try:
        StackBotDB.db.delete_metadata(key=key)
    except MetadataKeyNotFound as exc:
        raise click.ClickException(f'key ({key}) not found') from exc

@metadata.command('exists')
@key_option
def exists(key):
    """Test if a metadata key exists. Prints "true" or "false"."""
    StackBotDB.db.open()

    if StackBotDB.db.check_metadata(key=key):
        click.echo('true')
    else:
        click.echo('false')
