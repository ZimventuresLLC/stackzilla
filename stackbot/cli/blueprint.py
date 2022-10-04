"""Click handlers for the blueprint sub-command."""
import click

from stackbot.blueprint import Blueprint
from stackbot.database.base import StackBotDB

@click.group(name='blueprint')
def blueprint():
    """Command group for all blueprint CLI commands."""

@blueprint.command('apply')
@click.option('--path', required=True)
def apply(path):
    """Apply the on-disk blueprint."""
    StackBotDB.db.open()

    # TODO: Import the blueprint from disk
    disk_blueprint = Blueprint(path=path)
    disk_blueprint.load()

    disk_blueprint.verify()

    # TODO: Import the blueprint from the database
    # TODO: Diff the blueprint
    # TODO: Show the blueprint diff and ask for user confirmation
    # TODO: Appply the blueprint
    disk_blueprint.apply()

@blueprint.command('delete')
def delete():
    """Delete the blueprint"""
    StackBotDB.db.open()

    