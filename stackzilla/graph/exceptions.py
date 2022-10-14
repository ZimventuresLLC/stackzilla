"""Exceptions for the graph module."""
import typing
from typing import List

if typing.TYPE_CHECKING:
    from stackzilla.graph.graph import Node


class CircularDependency(Exception):
    """Raised when a circular dependency is encountered."""

    def __init__(self, *args: object) -> None:
        """Default constructor."""
        super().__init__(*args)

        # Holds a list of graph Node objects that were not resolved
        self.nodes: List['Node'] = []
