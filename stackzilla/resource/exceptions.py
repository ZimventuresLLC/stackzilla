"""Exceptions for the base resource class."""
from typing import Dict, List

from colorama import Fore, Style


class AttributeModifyFailure(Exception):
    """Raised when an attribute modification fails in an on_*_modified() handler."""

    def __init__(self, attribute_name: str, reason: str, *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)

        self.attribute_name: str = attribute_name
        self.reason: str = reason

class ResourceCreateFailure(Exception):
    """Raised when a resource creation fails."""

    def __init__(self, resource_name: str, reason: str, *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)

        self.resource_name: str = resource_name
        self.reason: str = reason

class ResourceDeleteFailure(Exception):
    """Raised when a resource deletion fails."""

    def __init__(self, resource_name: str, reason: str, *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)

        self.resource_name: str = resource_name
        self.reason: str = reason

class ResourceVerifyError(Exception):
    """Raised when a resource fails to verify."""

    def __init__(self, resource_name: str, *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)

        self.resource_name: str = resource_name
        self.attribute_errors: Dict[str, List[str]] = {}

    def add_attribute_error(self, name: str, error: str) -> None:
        """Add an attribute error to the current resource verification failure.

        Args:
            name (str): _description_
            error (str): _description_
        """
        # Create a list for the key, if one is not already present
        if name not in self.attribute_errors:
            self.attribute_errors[name] = []

        self.attribute_errors[name].append(error)

    def print(self):
        """Print out the exception."""
        print(Fore.RED + f'[{self.resource_name}]')

        for attr_name, attr_errors in self.attribute_errors.items():
            print(Fore.RED + f'!!{attr_name}')

            for error in attr_errors:
                print(Fore.RED + f'\t{error}')

        print(Style.RESET_ALL)
