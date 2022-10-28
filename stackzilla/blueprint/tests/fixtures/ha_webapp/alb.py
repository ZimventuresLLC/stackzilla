"""Defines a dummy ALB for the test blueprint."""
from stackzilla.provider.null.load_balancer import LoadBalancer

from .server import MyServer


class MyALB(LoadBalancer):
    """Dummy ALB."""

    def __init__(self) -> None:
        """Default constructur."""
        super().__init__()
        self.type = 'application'
        self.instances = [MyServer]
