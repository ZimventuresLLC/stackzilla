"""Module for database debugging CLI."""
import click

#from stackzilla.database.base import StackzillaDB
#from stackzilla.blueprint import StackzillaBlueprint
#from stackzilla.database.exceptions import ResourceNotFound

@click.group(name='database')
def database():
    """Command group for all database CLI commands."""

"""
@database.command('show-resource')
@click.option('--path', required=True)
def show_resource(path):
    StackzillaDB.db.open()

    # Load the blueprint from the database
    db_blueprint = StackzillaBlueprint()
    db_blueprint.load()

    try:
        resource = StackzillaDB.db.get_resource(path=path)
    except ResourceNotFound as exc:
        raise click.ClickException('Resource not found') from exc

    click.echo(resource)
"""
