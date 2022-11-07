"""Click handlers for the kubernetes sub-command."""
import click
from prettytable import PrettyTable

from stackzilla.cli.options import path_option
from stackzilla.cli.utils import get_resource_from_path


@click.group(name='kubernetes')
def kubernetes():
    """Command group for all compute CLI commands."""


@kubernetes.command('show')
@path_option
def show(path):
    """Show the details for a cluster."""
    resource = get_resource_from_path(path)

    click.echo('[endpoint]')
    click.echo(resource.endpoint)
    click.echo('[certificate authority data]')
    click.echo(resource.ca_data)

    # Print out all of hte nodes in the cluster
    click.echo('[nodes]')
    table = PrettyTable()
    node_data = resource.get_nodes()

    # The first row are the headers
    table.field_names = node_data[0]

    # The rest of the rows are the data
    table.add_rows(node_data[1:])
    click.echo(table)

@kubernetes.command('get-kubeconfig')
@path_option
def get_kubeconfig(path):
    """Generate a kubeconfig for the cluster."""
    resource = get_resource_from_path(path)

    click.echo(resource.get_kubeconfig())
