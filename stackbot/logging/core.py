"""Module for StackBot core component logging."""

from logging import CRITICAL, DEBUG, INFO, WARNING, Logger, getLogger
from typing import Optional


class CoreLogger:
    """Provide logging functionality for a core StackBot component."""

    def __init__(self, component: str):
        """Initialize a logging format and console handler.

        Args:
            component (str): Name of the functional component making the logging calls. ex: blueprint
        """
        self._component: str = component
        self._logger: Logger = getLogger(f'stackbot.{component}')

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
            extra = {'component': self._component}

        # Actually invoke the logger
        self._logger.log(level=level, msg=message, extra=extra)
