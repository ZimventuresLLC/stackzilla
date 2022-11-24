"""Click handlers for the compute sub-command."""
import click
from prettytable import PrettyTable
from pssh.clients.ssh import SSHClient

from stackzilla.cli.options import path_option
from stackzilla.cli.utils import get_resource_from_path
from stackzilla.host_services import HostServices
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
    resource: StackzillaCompute = get_resource_from_path(path=path, resource_type=StackzillaCompute)

    try:
        ssh_client = resource.ssh_connect()
    except SSHConnectError as exc:
        raise click.ClickException(f'Failed to connect: {str(exc)}') from exc

    output = ssh_client.run_command(command=command)
    for line in output.stdout:
        print(line)

@compute.command('get-ssh-key')
@path_option
def get_ssh_key(path):
    """Display the private SSH key for the specified host."""
    # Initialize the DB, load the blueprint, and snag the requested resource
    resource: StackzillaCompute = get_resource_from_path(path=path, resource_type=StackzillaCompute)
    click.echo(resource.ssh_credentials().key)

@compute.command('stop')
@path_option
@click.option('--wait/--no-wait', default=True, help='Wait for the shutdown to complete')
def stop(path, wait):
    """Power down the compute."""
    # Initialize the DB, load the blueprint, and snag the requested resource
    resource: StackzillaCompute = get_resource_from_path(path=path, resource_type=StackzillaCompute)
    resource.stop(wait_for_offline=wait)

@compute.command('start')
@path_option
@click.option('--wait/--no-wait', default=True, help='Wait for the start to complete')
def start(path, wait):
    """Power down the compute."""
    # Initialize the DB, load the blueprint, and snag the requested resource
    resource: StackzillaCompute = get_resource_from_path(path=path, resource_type=StackzillaCompute)
    resource.start(wait_for_online=wait)

@compute.command('show')
@path_option
def show(path):
    """Show information about the host."""
    # Setup the Database, load the blueprint, and get the resource
    resource: StackzillaCompute = get_resource_from_path(path, resource_type=StackzillaCompute)

    # Connect to the host to get information
    client: SSHClient = resource.ssh_connect()
    host_services: HostServices = HostServices(ssh_client=client)

    table = PrettyTable()

    # The first row are the headers
    table.field_names = ['OS Name', 'OS Version', 'Is POSIX', 'Linux Distro', 'Package Manager(s)', 'SSH IP']

    # Build a list of the package managers
    pkg_mgr_names = [mgr.name() for mgr in host_services.package_managers]

    # The rest of the rows are the data
    table.add_row([host_services.os_name, host_services.os_version,
                   host_services.is_posix, host_services.linux_distro, pkg_mgr_names, resource.ssh_address().host])

    # Print it out!
    click.echo(table)
