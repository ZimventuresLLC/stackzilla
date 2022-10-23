"""Descriptor which defines any attribute for a Resource class."""
# See https://docs.python.org/3/glossary.html#term-descriptor for details on descriptors

from typing import Any, List, Type

from stackzilla.utils.numbers import StackzillaRange


# pylint: disable=too-many-instance-attributes
class StackzillaAttribute:
    """Descriptor class for all blueprint attributes."""

    # pylint: disable=too-many-arguments
    def __init__(self, required: bool = False, default: Any = None, choices: List[Any] = None, types: List[Type] = None,
                 modify_rebuild: bool = False, dynamic: bool = False, secret: bool = False, number_range: StackzillaRange = None):
        """Constructor for the attribute.

        Args:
            required (bool, optional): Indicates if the attribute must be defined. Defaults to False.
            default (Any, optional): The value for the parameter if none is specified. Defaults to None.
            choices (List[Any], optional): List of valid values for the parameter. Defaults to None.
            types (List[Type], optional): List of types that are allowed for the attribute
            modify_rebuild (bool, optional): Rebuild the resource if true and parameter is modified. Defaults to False.
            number_range (StackzillaRange, optional): Minimum and maximum allowable int or float values. Defaults to None.
            dynamic (bool, optional): The parameter is set programatically and not by the user. Defaults to False.
            secret (bool, optional): Parameter holds sensitive information. Defaults to False.
        """
        self.choices = choices
        self.default = default
        self.dynamic = dynamic
        self.modify_rebuild = modify_rebuild
        self.number_range = number_range
        self.required = required
        self.secret = secret
        self.types = types

    def __set_name__(self, owner, name):
        """Called by Python to let the descriptor class know the parameter name holding this class."""
        self.name = name # pylint: disable=attribute-defined-outside-init

    def __set__(self, instance, value):
        """Called by Python to set the value of the parameter."""
        instance.__dict__[self.name] = value

    def __get__(self, instance, _owner):
        """Called by Python to fetch the value of the parameter."""
        if instance is None:
            return self

        if self.name not in instance.__dict__:
            return self.default

        return instance.__dict__[self.name]
