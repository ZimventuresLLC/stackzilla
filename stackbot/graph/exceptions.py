"""Exceptions for the graph module."""
from typing import List


class CircularDependency(Exception):
    """Raised when a circular dependency is encountered."""

    def __init__(self, *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)

        # Holds a list of graph Node objects that were not resolved
        self.nodes: List['Node'] = []
