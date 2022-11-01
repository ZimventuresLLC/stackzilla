"""Dummy instance for the ha_webapp blueprint."""
from stackzilla.provider.null.instance import Instance


class MyServer(Instance):
    """Dummy instance which uses the NULL provider."""

    def __init__(self) -> None:
        """Default constructor."""
        super().__init__()
        self.type = 'large'
        self.create_failure = False
