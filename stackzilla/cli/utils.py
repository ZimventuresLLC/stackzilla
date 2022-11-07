"""CLI Utilities."""
import click

from stackzilla.blueprint import StackzillaBlueprint
from stackzilla.database.base import StackzillaDB
from stackzilla.database.exceptions import ResourceNotFound
from stackzilla.resource import StackzillaResource
from stackzilla.utils.constants import DISK_BP_PREFIX


def get_resource_from_path(path: str) -> StackzillaResource:
    """Connect to the host via SSH."""
    StackzillaDB.db.open()

    # Import the blueprint from disk
    db_blueprint = StackzillaBlueprint(python_root=DISK_BP_PREFIX)
    db_blueprint.load()

    # Load the resource specified by path
    try:
        resource: StackzillaResource = db_blueprint.get_resource(path=path)
        resource = resource()
        resource.load_from_db()
        return resource
    except ResourceNotFound as exc:
        raise click.ClickException('Resource specified by path not found') from exc
