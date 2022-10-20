"""Module for numerical utilities in Stackzilla."""
from dataclasses import dataclass
from typing import Union


@dataclass
class StackzillaRange:
    """Defines the minimum and maximum values for an attribute range check."""

    min: Union[int, float]
    max: Union[int, float]

    def in_range(self, value: Union[int, float]) -> bool:
        """Test if the specified value is within the range.

        Args:
            value (Union[int, float]): The value to test

        Returns:
            bool: True if the value is within the range, False otherwise.
        """
        return self.min <= value <= self.max
