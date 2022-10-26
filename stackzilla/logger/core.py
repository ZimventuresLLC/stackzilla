"""Module for Stackzilla core component logging."""
from typing import Optional

from stackzilla.logger.base import BaseLogger


class CoreLogger(BaseLogger):
    """Provide logging functionality for a core Stackzilla component."""

    def __init__(self, component: str):
        """Initialize a logging format and console handler.

        Args:
            component (str): Name of the functional component making the logging calls. ex: blueprint
        """
        self._component: str = component
        super().__init__(name=f'stackzilla.{component}')

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
        else:
            extra['component'] = self._component

        super()._log(message, level, extra)
