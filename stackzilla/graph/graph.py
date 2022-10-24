"""Module for graph resolution functionality."""
from dataclasses import dataclass
from typing import Dict, List, Type

from stackzilla.graph.exceptions import CircularDependency
from stackzilla.logger.core import CoreLogger


@dataclass
class Node:
    """Represents a single node within the graph."""

    obj: Type[object]
    dependencies: List[Type[object]]

    def has_dependencies(self):
        """Test if the node has any dependencies."""
        return bool(self.dependencies)

class Graph:
    """Implements a graph resolver for class dependencies."""

    def __init__(self) -> None:
        """Default constructor."""
        # Dictionary of all the graph nodes. Each entry is indexed by the
        # id() of the Node.obj (which is an int)
        self._nodes: Dict[int, Node] = {}
        self._logger = CoreLogger(component='graph')

    def add_node(self, obj: Type[object], dependencies: List[Type[object]]):
        """Add a node to the graph.

        Args:
            obj (Type[object]): The class to add to the graph
            dependencies (List[Type[object]]): A list of classes that obj depends on.
        """
        self._logger.debug(f'Adding node {id(obj)}')
        self._nodes[id(obj)] = Node(obj=obj, dependencies=dependencies)


    def resolve(self, reverse: bool = False) -> List[List[Type[object]]]:
        """Resolve the graph into phases.

        Args:
            reverse (bool, optional): If True, resolve the graph in reverse order. Defaults to False.

        Raises:
            CircularDependency: Raised if a circular dependency is detected.

        Returns:
            List[List[Type[object]]]: _description_
        """
        # Holds the results of the resolved graph
        # Each top level list item is a "phase".
        # Objects within a phase do not depend on each other.
        phases: List[List[object]] = []

        # Create a copy of the nodes dictionary since we'll be removing entries from it
        nodes: Dict[int, Node] = self._nodes.copy()

        # List of objects for the current phase
        current_phase: List[Type[object]] = []

        # Work until there's nothing left to do!
        while nodes:

            # Flag that indicates if nodes were deleted on the current pass
            nodes_deleted = False

            # Walk through all of the nodes in the graph, looking for entries with no dependencies
            for node in nodes.values():

                # If this node has no dependencies, add it to the current phase.
                if node.has_dependencies() is False:
                    current_phase.append(node.obj)

            # Go back and remove all of the nodes from the current phase
            for node in current_phase:
                nodes_deleted = True

                # Remove this node from the graph to ensure it isn't considered for future phases
                del nodes[id(node)]

            # Re-walk the remaining nodes in the graph to remove dependencies
            for dependent_node in nodes.values():

                # For all of the nodes in the current phase, remove them as dependencies
                for node in current_phase:
                    if node in dependent_node.dependencies:
                        dependent_node.dependencies.remove(node)

            # Ruh-roh! If no nodes were deleted, that means a circular dependency was encountered
            if nodes_deleted is False and nodes:

                error = CircularDependency()

                for node in nodes.values():
                    error.nodes.append(node)

                raise error

            # Add the current phase to the list of phases and empty the phase list to prepare for the next one
            phases.append(current_phase)
            current_phase = []

        # Does the caller want to see the graph in reverse?
        if reverse:
            phases.reverse()

        return phases
