"""Module for database debugging CLI."""
import pprint

import click

from stackzilla.cli.utils import get_resource_from_path

from .options import path_option


@click.group(name='database')
def database():
    """Command group for all database CLI commands."""

@database.command('show-resource')
@path_option
def show_resource(path):
    """Show a resource, and its attributes, as it is in the database."""
    resource = get_resource_from_path(path=path)

    print(resource.path(remove_prefix=True))
    print(f'Version: {resource.version()}')
    print(f'Saved version: {resource.saved_version()}')
    pprint.pprint(resource.__dict__)
