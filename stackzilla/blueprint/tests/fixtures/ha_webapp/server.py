from stackzilla.provider.null.instance import Instance

class MyServer(Instance):
    def __init__(self) -> None:
        super().__init__()
        self.type = 'large'
        self.create_failure = False
