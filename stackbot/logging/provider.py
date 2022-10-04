"""Module for StackBot provider logging."""

from logging import CRITICAL, DEBUG, INFO, WARNING, Logger, getLogger
from typing import Optional


class ProviderLogger:
    """Logging functionality for a StackBot provider module."""

    def __init__(self, provider_name: str, resource_name: str):
        """Initialize a logging format and console handler.

        Args:
            component (str): Name of the functional component making the logging calls. ex: blueprint
        """
        self._provider_name: str = provider_name
        self._resource_name: str = resource_name
        self._logger: Logger = getLogger(self._provider_name)

    def log(self, message: str, extra: Optional[dict] = None) -> None:
        """Log an INFO level message.

        Args:
            message (str): Message to log
            extra (Optional[dict], optional): Optional data to log with the message. Defaults to None.
        """
        self._log(message=message, extra=extra, level=INFO)

    def warning(self, message: str, extra: Optional[dict] = None) -> None:
        """Log a WARNING level message.

        Args:
            message (str): Message to log
            extra (Optional[dict], optional): Optional data to log with the message. Defaults to None.
        """
        self._log(message=message, extra=extra, level=WARNING)

    def debug(self, message: str, extra: Optional[dict] = None) -> None:
        """Log a DEBUG level message.

        Args:
            message (str): Message to log
            extra (Optional[dict], optional): Optional data to log with the message. Defaults to None.
        """
        self._log(message=message, extra=extra, level=DEBUG)

    def critical(self, message: str, extra: Optional[dict] = None) -> None:
        """Log a CRITICAL level message.

        Args:
            message (str): Message to log
            extra (Optional[dict], optional): Optional data to log with the message. Defaults to None.
        """
        self._log(message=message, extra=extra, level=CRITICAL)

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

        # Actually invoke the logger
        self._logger.log(level=level, msg=message, extra=extra)
