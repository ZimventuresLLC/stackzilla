"""Module for common Click options."""
import click

from stackzilla.cli._callbacks import namespace_callback


def namespace_option(function):
    """Decorator for the namesapce CLI argument."""
    function = click.option(
        '--namespace',
        required=True,
        expose_value=True,
        callback=namespace_callback,
        help='Text name for the new work environment')(function)
    return function

def key_option(function):
    """Decorator for the metadata key CLI argument."""
    function = click.option('--key', required=True, help='Metadata key to index by')(function)
    return function


def value_option(function):
    """Decorator for the metadata value CLI argument."""
    function = click.option('--value', required=True, help='Metadata value to set')(function)
    return function
