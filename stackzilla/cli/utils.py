"""CLI Utilities."""
from typing import Optional, Type

import click

from stackzilla.blueprint import StackzillaBlueprint
from stackzilla.database.base import StackzillaDB
from stackzilla.database.exceptions import ResourceNotFound
from stackzilla.resource import StackzillaResource
from stackzilla.utils.constants import DISK_BP_PREFIX


def get_resource_from_path(path: str, resource_type: Optional[Type]=StackzillaResource) -> StackzillaResource:
    """Connect to the host via SSH."""
    StackzillaDB.db.open()

    # Import the blueprint from disk
    db_blueprint = StackzillaBlueprint(python_root=DISK_BP_PREFIX)
    db_blueprint.load()

    # Load the resource specified by path
    try:
        resource: StackzillaResource = db_blueprint.get_resource(path=path)
        obj = resource.from_db()

        # Perform a type check
        if issubclass(obj.__class__, resource_type) is False:
            raise click.ClickException(f'{obj.path()} is not a {resource_type} resource.')

        return obj
    except ResourceNotFound as exc:
        raise click.ClickException('Resource specified by path not found') from exc
