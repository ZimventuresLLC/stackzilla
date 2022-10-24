"""Interface for concrete logging classes."""
from logging import CRITICAL, DEBUG, INFO, WARNING, Logger, getLogger
from typing import Optional


class BaseLogger:
    """Base interface for the core and provider loggers."""

    def __init__(self, name: str) -> None:
        """Get the Python logging object based on the provided name.

        Args:
            name (str): _description_
        """
        self._logger: Logger = getLogger(name)

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
        # Actually invoke the logger
        self._logger.log(level=level, msg=message, extra=extra)
