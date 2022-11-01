"""Click handlers for the compute sub-command."""
import click

from stackzilla.cli.options import path_option
from stackzilla.cli.utils import get_resource_from_path
from stackzilla.resource.compute import StackzillaCompute
from stackzilla.resource.compute.exceptions import SSHConnectError


@click.group(name='compute')
def compute():
    """Command group for all compute CLI commands."""


@compute.command('ssh')
@path_option
@click.argument('command')
def ssh(path, command):
    """Execute the specified command on the resoruce via SSH."""
    # Initialize the DB, load the blueprint, and snag the requested resource
    resource: StackzillaCompute = get_resource_from_path(path=path)

    if issubclass(resource.__class__, StackzillaCompute) is False:
        raise click.ClickException(f'{resource.path()} is not a StackzillaCompute resource.')
    try:
        ssh_client = resource.ssh_connect()
    except SSHConnectError as exc:
        raise click.ClickException(f'Failed to connect: {str(exc)}') from exc

    output = ssh_client.run_command(command)
    for line in output.stdout:
        print(line)

@compute.command('stop')
@path_option
@click.option('--wait/--no-wait', default=True, help='Wait for the shutdown to complete')
def stop(path, wait):
    """Power down the compute."""
    # Initialize the DB, load the blueprint, and snag the requested resource
    resource: StackzillaCompute = get_resource_from_path(path=path)

    if issubclass(resource.__class__, StackzillaCompute) is False:
        raise click.ClickException(f'{resource.path()} is not a StackzillaCompute resource.')

    resource.stop(wait_for_offline=wait)

@compute.command('start')
@path_option
@click.option('--wait/--no-wait', default=True, help='Wait for the start to complete')
def start(path, wait):
    """Power down the compute."""
    # Initialize the DB, load the blueprint, and snag the requested resource
    resource: StackzillaCompute = get_resource_from_path(path=path)

    if issubclass(resource.__class__, StackzillaCompute) is False:
        raise click.ClickException(f'{resource.path()} is not a StackzillaCompute resource.')

    resource.start(wait_for_online=wait)
