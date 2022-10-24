"""Testing."""
# pylint: skip-file
from stackzilla.resource.base import StackzillaResource

from .a.a import A


class Root(A):
    """Testing."""

class MyThing(StackzillaResource):
    """Testing."""
