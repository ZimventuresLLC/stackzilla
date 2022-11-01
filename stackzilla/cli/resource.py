"""Click handlers for the resource sub-command."""
import click

from stackzilla.blueprint import StackzillaBlueprint
from stackzilla.cli.options import path_option
from stackzilla.database import StackzillaDB
from stackzilla.database.exceptions import ResourceNotFound
from stackzilla.resource.base import StackzillaResource
from stackzilla.utils.constants import DISK_BP_PREFIX


@click.group(name='resource')
def resource():
    """Command group for all resource CLI commands."""


@resource.command('show')
@path_option
def show(path):
    """Connect to the host via SSH."""
    StackzillaDB.db.open()

    # Import the blueprint from disk
    db_blueprint = StackzillaBlueprint(python_root=DISK_BP_PREFIX)
    db_blueprint.load()

    # Load the resource specified by path
    try:
        resource_obj: StackzillaResource = db_blueprint.get_resource(path=path)
        resource_obj = resource_obj()
        resource_obj.load_from_db()
    except ResourceNotFound as exc:
        raise click.ClickException('Resource specified by path not found') from exc

    print(f'[{resource_obj.path(remove_prefix=True)}]')

    for name, attribute in resource_obj.attributes.items():
        value = getattr(resource_obj, name)

        if attribute.secret:
            value = '<secret>'
        print(f'{name}: {value}')
