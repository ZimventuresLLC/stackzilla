"""Click handlers for the blueprint sub-command."""
from io import StringIO
from typing import List, Type

import click

from stackzilla.blueprint import StackzillaBlueprint
from stackzilla.blueprint.exceptions import BlueprintVerifyFailure
from stackzilla.database.base import StackzillaDB
from stackzilla.diff import StackzillaDiff, StackzillaDiffResult
from stackzilla.graph import Graph

@click.group(name='blueprint')
def blueprint():
    """Command group for all blueprint CLI commands."""

@blueprint.command('apply')
@click.option('--path', required=True)
def apply(path):
    """Apply the on-disk blueprint."""
    StackzillaDB.db.open()

    # Import the blueprint from disk
    disk_blueprint = StackzillaBlueprint(path=path)
    disk_blueprint.load()

    # Verify the on-disk blueprint
    try:
        disk_blueprint.verify()
    except BlueprintVerifyFailure as verify_error:

        for error in verify_error.errors:
            error.print()

        raise click.ClickException('On-disk Blueprint verification failed')

    # Import the blueprint from the database and verify it
    db_blueprint = StackzillaBlueprint()
    db_blueprint.load()

    try:
        db_blueprint.verify()
    except BlueprintVerifyFailure as verify_error:

        for error in verify_error.errors:
            error.print()

        raise click.ClickException('Database Blueprint verification failed')

    # Diff the blueprint
    diff = StackzillaDiff()
    diff.diff(source=disk_blueprint, destination=db_blueprint)

    # Show the diff and prompt the user
    if diff.result.result != StackzillaDiffResult.SAME:

        # Print the diff into a temporary buffer, then output it to the console
        output_buffer = StringIO()
        diff.print(output_buffer)
        click.echo(output_buffer.getvalue())

        if click.confirm('Apply Changes?'):
            diff.apply()
    else:
        click.echo('No differences')

@blueprint.command('verify')
@click.option('--path', required=True)
def verify_blueprint(path):
    """Verify the on-disk blueprint"""

    disk_blueprint = StackzillaBlueprint(path=path)
    disk_blueprint.load()

    try:
        disk_blueprint.verify()
    except BlueprintVerifyFailure as verify_error:

        for error in verify_error.errors:
            error.print()

        raise click.ClickException('Blueprint verification failed')

    click.echo('Verified')

@blueprint.command('diff')
@click.option('--path', required=True, help='Full or relative path to the on-disk blueprint')
@click.option('--verify/--no-verify', default=False, is_flag=True, help='Verify blueprints before diffing them')
def diff_blueprints(path, verify):
    """Show a diff of the on-disk and database blueprints."""

    StackzillaDB.db.open()

    # Import the blueprint from disk and database
    disk_blueprint = StackzillaBlueprint(path=path)
    disk_blueprint.load()

    db_blueprint = StackzillaBlueprint()
    db_blueprint.load()

    # Verify the on-disk blueprint
    if verify:
        try:
            disk_blueprint.verify()
        except BlueprintVerifyFailure as verify_error:

            for error in verify_error.errors:
                error.print()

            raise click.ClickException('On-disk Blueprint verification failed')

        try:
            db_blueprint.verify()
        except BlueprintVerifyFailure as verify_error:

            for error in verify_error.errors:
                error.print()

            raise click.ClickException('Database Blueprint verification failed')

    # Diff the blueprint
    diff = StackzillaDiff()
    diff.diff(source=disk_blueprint, destination=db_blueprint)

    # Show the diff and prompt the user
    if diff.result.result != StackzillaDiffResult.SAME:

        # Print the diff into a temporary buffer, then output it to the console
        output_buffer = StringIO()
        diff.print(output_buffer)
        click.echo(output_buffer.getvalue())
    else:
        click.echo('No differences')

@blueprint.command('delete')
def delete():
    """Delete the blueprint."""
    StackzillaDB.db.open()

    # Load the blueprint from disk
    db_blueprint = StackzillaBlueprint()
    db_blueprint.load()

    if click.confirm('Delete blueprint?') is False:
        return

    # Show the blueprint

    graph: Graph = db_blueprint.build_graph()
    phases: List[List[Type[object]]] = graph.resolve(reverse=True)

    for phase in phases:
        # TODO: make each phase multi-threaded

        for resource in phase:
            obj = resource()
            obj.delete()

    # Delete all of the blueprint information from the database
    StackzillaDB.db.delete_all_blueprint_packages()
    StackzillaDB.db.delete_all_blueprint_modules()
