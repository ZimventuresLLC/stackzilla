"""Click handlers for the compute sub-command."""
import click

from stackzilla.blueprint import StackzillaBlueprint
from stackzilla.blueprint.exceptions import ResourceNotFound
from stackzilla.cli.options import path_option
from stackzilla.database.base import StackzillaDB
from stackzilla.resource.compute import StackzillaCompute
from stackzilla.resource.compute.exceptions import SSHConnectError
from stackzilla.utils.constants import DISK_BP_PREFIX


@click.group(name='compute')
def compute():
    """Command group for all compute CLI commands."""


@compute.command('ssh')
@path_option
@click.argument('command')
def ssh(path, command):
    """Connect to the host via SSH."""
    StackzillaDB.db.open()

    # Import the blueprint from disk
    db_blueprint = StackzillaBlueprint(python_root=DISK_BP_PREFIX)
    db_blueprint.load()

    # Load the resource specified by path
    try:
        resource: StackzillaCompute = db_blueprint.get_resource(path=path)
        resource = resource()
        resource.load_from_db()
    except ResourceNotFound as exc:
        raise click.ClickException('Resource specified by path not found') from exc

    if issubclass(resource.__class__, StackzillaCompute) is False:
        raise click.ClickException(f'{resource.path()} is not a StackzillaCompute resource.')
    try:
        ssh_client = resource.ssh_connect()
    except SSHConnectError as exc:
        raise click.ClickException(f'Failed to connect: {str(exc)}') from exc

    output = ssh_client.run_command(command)
    for line in output.stdout:
        print(line)
