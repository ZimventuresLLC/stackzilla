"""Dummy volume for the test blueprint."""
from stackzilla.provider.null.volume import Volume

from .server import MyServer


class MyVol(Volume):
    """A dummy volume for testing."""

    def __init__(self) -> None:
        """The constructor."""
        super().__init__()
        self.size = 128
        self.instance = MyServer
        self.create_failure = False
