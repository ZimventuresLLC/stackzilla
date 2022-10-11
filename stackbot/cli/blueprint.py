"""Click handlers for the blueprint sub-command."""
import click
from io import StringIO

from stackbot.blueprint import StackBotBlueprint
from stackbot.database.base import StackBotDB
from stackbot.diff import StackBotDiff, StackBotBlueprintDiff
from stackbot.diff.diff import StackBotDiffResult

@click.group(name='blueprint')
def blueprint():
    """Command group for all blueprint CLI commands."""

@blueprint.command('apply')
@click.option('--path', required=True)
def apply(path):
    """Apply the on-disk blueprint."""
    StackBotDB.db.open()

    # TODO: Import the blueprint from disk
    disk_blueprint = StackBotBlueprint(path=path)
    disk_blueprint.load()
    disk_blueprint.verify()

    # TODO: Import the blueprint from the database
    db_blueprint = StackBotBlueprint()
    db_blueprint.load()
    db_blueprint.verify()

    # TODO: Diff the blueprint
    diff = StackBotDiff()
    diff.diff(source=disk_blueprint, destination=db_blueprint)

    # Show the diff and prompt the user
    if diff.result.result != StackBotDiffResult.SAME:

        # Print the diff into a temporary buffer, then output it to the console
        output_buffer = StringIO()
        diff.print(output_buffer)
        click.echo(output_buffer.getvalue())

        if click.confirm('Apply Changes?'):
            diff.apply()


@blueprint.command('delete')
def delete():
    """Delete the blueprint"""
    StackBotDB.db.open()
