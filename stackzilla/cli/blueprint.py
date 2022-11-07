"""Click handlers for the blueprint sub-command."""
from io import StringIO
from typing import List, Type

import click

from stackzilla.blueprint import StackzillaBlueprint
from stackzilla.blueprint.exceptions import BlueprintVerifyFailure
from stackzilla.cli.options import blueprint_path, dry_run_option
from stackzilla.database.base import StackzillaDB
from stackzilla.database.exceptions import DatabaseNotFound, ResourceNotFound
from stackzilla.diff import StackzillaDiff, StackzillaDiffResult
from stackzilla.diff.exceptions import (ApplyErrors,
                                        UnhandledAttributeModifications,
                                        VersionIncompatibility)
from stackzilla.graph import Graph
from stackzilla.utils.constants import DISK_BP_PREFIX


@click.group(name='blueprint')
def blueprint():
    """Command group for all blueprint CLI commands."""

# pylint: disable=too-many-branches
@blueprint.command('apply')
@blueprint_path
def apply(path):
    """Apply the on-disk blueprint."""
    try:
        StackzillaDB.db.open()
    except DatabaseNotFound as exc:
        raise click.ClickException('No database found.') from exc

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
    try:
        diff.diff(source=disk_blueprint, destination=db_blueprint)
    except VersionIncompatibility as exc:
        raise click.ClickException(str(exc))

    # Show the diff and prompt the user
    if diff.result.result != StackzillaDiffResult.SAME:

        # Print the diff into a temporary buffer, then output it to the console
        output_buffer = StringIO()
        diff.print(output_buffer)
        click.echo(output_buffer.getvalue())

        if click.confirm('Apply Changes?'):
            try:
                diff.apply()
            except ApplyErrors as exc:
                for error in exc.errors:
                    click.echo(error)
                raise click.ClickException('Apply failed - see errors above.')
            except UnhandledAttributeModifications as exc:
                for attr in exc.unhandled_attributes:
                    click.echo(f'ERROR: Unhandled attribute modification - {attr.name}')
                    raise click.ClickException(
                        'Unhanlded attribute modifications. Please contact the provider author and report this bug.')

    else:
        click.echo('No differences')

@blueprint.command('verify')
@click.option('--path', required=True)
def verify_blueprint(path):
    """Verify the on-disk blueprint."""
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

    try:
        diff.diff(source=disk_blueprint, destination=db_blueprint)
    except VersionIncompatibility as exc:
        raise click.ClickException(str(exc))

    # Show the diff and prompt the user
    if diff.result.result != StackzillaDiffResult.SAME:

        # Print the diff into a temporary buffer, then output it to the console
        output_buffer = StringIO()
        diff.print(output_buffer)
        click.echo(output_buffer.getvalue())
    else:
        click.echo('No differences')

@blueprint.command('delete')
@dry_run_option
def delete(dry_run):
    """Delete the blueprint."""
    StackzillaDB.db.open()

    # Load the blueprint from the database
    # NOTE: The disk blueprint is not being imported so we must import the database blueprint INTO the
    # disk blueprint's python namespace root. That's because all of the resources are pickled before
    # persistance FROM the disk blueprint's namespace.
    db_blueprint = StackzillaBlueprint(python_root=DISK_BP_PREFIX)
    db_blueprint.load()

    if click.confirm('Delete blueprint?') is False:
        return

    # Show the blueprint
    graph: Graph = db_blueprint.build_graph()
    phases: List[List[Type[object]]] = graph.resolve(reverse=True)

    for phase in phases:

        resources_in_phase = []
        for resource in phase:
            resources_in_phase.append(resource.path(remove_prefix=True))
        click.echo(f'Resources in this deletion phase {resources_in_phase}')

        for resource in phase:
            obj = resource()

            try:
                obj.load_from_db()
            except ResourceNotFound:
                # The resource was not found likely due to it not being correctly applied previously.
                click.echo(f'{obj.path(remove_prefix=True)} was not in the database. Skipping.')
                continue

            if dry_run is False:
                obj.delete()
            else:
                click.echo(f'Dry Run enabled: skipping deletion of {resource.path()}')

    # Delete all of the blueprint information from the database
    if dry_run is False:
        StackzillaDB.db.delete_all_blueprint_packages()
        StackzillaDB.db.delete_all_blueprint_modules()
