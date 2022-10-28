from stackzilla.provider.null.volume import Volume
from .server import MyServer

class MyVol(Volume):
    def __init__(self) -> None:
        super().__init__()
        self.size = 64
        self.instance = MyServer
        self.create_failure = False
