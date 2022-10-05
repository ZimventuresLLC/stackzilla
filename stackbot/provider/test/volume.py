from typing import List
from stackbot.resource.base import StackBotResource, ResourceVersion
from stackbot.attribute.attribute import StackBotAttribute
from stackbot.logging.provider import ProviderLogger

class Volume(StackBotResource):
    """Dummy volume resource."""
    size = StackBotAttribute(required=True)

    def __init__(self) -> None:
        super().__init__()
        self._logger = ProviderLogger(provider_name='stackbot-test:volume', resource_name=self.path())

    def create(self) -> None:
        self._logger.debug(message="Creating volume")
        return super().create()

    def verify(self) -> None:
        return super().verify()

    def depends_on(self) -> List['StackBotResource']:
        return super().depends_on()

    @classmethod
    def version(cls) -> ResourceVersion:
        return ResourceVersion(major=1, minor=0, build=0, name='FCS')