"""Exceptions for the Stackzilla compute module."""

class SSHConnectError(Exception):
    """Raised when SSH fails to connect."""

class ComputeStartError(Exception):
    """Raised by StackzillaCompute.start on failure."""

class ComputeStopError(Exception):
    """Raised by StackzillaCompute.stop on failure."""
