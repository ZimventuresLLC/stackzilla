"""Click handlers for the kubernetes sub-command."""
import click

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
