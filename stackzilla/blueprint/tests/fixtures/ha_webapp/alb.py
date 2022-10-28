from stackzilla.provider.null.load_balancer import LoadBalancer
from .server import MyServer

class MyALB(LoadBalancer):
    def __init__(self) -> None:
        super().__init__()
        self.type = 'application'
        self.instances = [MyServer]
