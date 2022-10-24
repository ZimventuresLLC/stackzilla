"""Module for Stackzilla provider logging."""

from typing import Optional

from stackzilla.logger.base import BaseLogger


class ProviderLogger(BaseLogger):
    """Logging functionality for a Stackzilla provider module."""

    def __init__(self, provider_name: str, resource_name: str):
        """Initialize a logging format and console handler.

        Args:
            provider_name (str): The name of the provider that is performing the logging. Ex: "Apache"
            resource_name (str): Name of the resource that is being logged (generally should be self.path())
        """
        self._provider_name: str = provider_name
        self._resource_name: str = resource_name
        super().__init__(name=self._provider_name)

    def _log(self, message: str, level: int, extra: Optional[dict] = None) -> None:
        """Private method which will add the component to the extra data and invoke the Python logger.

        Args:
            message (str): _description_
            level (int): _description_
            extra (Optional[dict], optional): _description_. Defaults to None.
        """
        # Add the component to the extra data
        if extra is None:
            extra = {'provider': self._provider_name, 'resource_name': self._resource_name}

        super()._log(message=message, level=level, extra=extra)
