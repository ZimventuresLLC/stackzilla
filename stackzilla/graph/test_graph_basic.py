"""Tests for the graph module."""
# pylint: disable=too-few-public-methods
import pytest

from stackzilla.graph import Graph
from stackzilla.graph.exceptions import CircularDependency


class Alpha:
    """Dummy class."""

class Beta:
    """Dummy class."""

class Charlie:
    """Dummy class."""


def test_graph_no_dependencies():
    """Verify that a graph with no dependencies yields a single phase."""
    graph = Graph()

    # Add 3 classes to the graph, each has no dependencies
    for obj in [Alpha, Beta, Charlie]:
        graph.add_node(obj=obj, dependencies=[])

    results = graph.resolve()

    # There should only be a single phase
    assert len(results) == 1

    # Ensure all 3 classes are in the phase
    for obj in [Alpha, Beta, Charlie]:
        assert obj in results[0]

def test_single_phase_with_circular_dependency():
    """Verify a basic circular dependency."""
    graph = Graph()

    # Each class depends on each other. This graph can never be resolved.
    graph.add_node(obj=Alpha, dependencies=[Beta])
    graph.add_node(obj=Beta, dependencies=[Alpha])

    # Verify the exception is raised and that it has the correct contents
    with pytest.raises(CircularDependency) as exc:
        graph.resolve()

        # There should be two Node objects in the 'nodes' parameter of the exception
        assert len(exc.nodes) == 2

        # Make sure that the two classes in the exception match the two classes that were passed in
        error_objects = [exec.nodes[0].obj, exec.nodes[1].obj]
        assert error_objects == [Alpha, Beta]

def test_multiple_phases_with_circular_dependency():
    """Verify that a second phase with a circular dependency will be appropriately flagged"""
    graph = Graph()
    graph.add_node(obj=Alpha, dependencies=[])
    graph.add_node(obj=Beta, dependencies=[Charlie])
    graph.add_node(obj=Charlie, dependencies=[Beta])

    with pytest.raises(CircularDependency) as exc:
        graph.resolve()

        # There should be two graph nodes that were left unresolved
        assert len(exc.nodes) == 2

        # Make sure that the two classes in the exception match the two classes that were passed in
        error_objects = [exec.nodes[0].obj, exec.nodes[1].obj]
        assert error_objects == [Beta, Charlie]

def test_multiple_phases():
    """Ensure that a multi-phased graph is resolved correctly."""

    graph = Graph()
    graph.add_node(obj=Alpha, dependencies=[Beta])
    graph.add_node(obj=Beta, dependencies=[Charlie])
    graph.add_node(obj=Charlie, dependencies=[])

    result = graph.resolve()

    # Verify there are 3 phases
    assert len(result) == 3

    # Verify there is only a single class in each phase
    for phase in result:
        assert len(phase) == 1

    # Verify the contents of each phase
    assert result[0][0] == Charlie
    assert result[1][0] == Beta
    assert result[2][0] == Alpha

def test_phase_reversal():
    """Verify that the graph resolution is reversed when requested"""
    graph = Graph()
    graph.add_node(obj=Alpha, dependencies=[Beta])
    graph.add_node(obj=Beta, dependencies=[Charlie])
    graph.add_node(obj=Charlie, dependencies=[])

    result = graph.resolve(reverse=True)
    # Verify the contents of each phase
    assert result[0][0] == Alpha
    assert result[1][0] == Beta
    assert result[2][0] == Charlie
