"""Module for common Click options."""
import click

from stackzilla.cli._callbacks import namespace_callback


def dry_run_option(function):
    """Do everything but actually execute the operation."""
    function = click.option('--dry-run/--no-dry-run', help='Skip performing the operation')(function)
    return function

def namespace_option(function):
    """Decorator for the namesapce CLI argument."""
    function = click.option(
        '--namespace',
        required=True,
        expose_value=True,
        callback=namespace_callback,
        help='Text name for the new work environment')(function)
    return function

def path_option(function):
    """Decorator for any CLI command which takes the path to a blueprint resource."""
    function = click.option('--path', required=True, help='Python path to the blueprint resource')(function)
    return function

def blueprint_path(function):
    """Decorator for any CLI command which takes a blueprint file system path."""
    function = click.option('--path', required=True,
                            type=click.Path(exists=True), help='File system path to the blueprint')(function)
    return function

def key_option(function):
    """Decorator for the metadata key CLI argument."""
    function = click.option('--key', required=True, help='Metadata key to index by')(function)
    return function


def value_option(function):
    """Decorator for the metadata value CLI argument."""
    function = click.option('--value', required=True, help='Metadata value to set')(function)
    return function
