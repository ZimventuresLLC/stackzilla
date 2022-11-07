"""Module for base compute functionality."""
import time
from abc import abstractmethod
from dataclasses import dataclass

from pssh.clients import SSHClient

from stackzilla.resource.base import StackzillaResource
from stackzilla.resource.compute.exceptions import SSHConnectError


@dataclass
class SSHCredentials:
    """Model for SSH credentials."""

    username: str
    password: str
    key: str

@dataclass
class SSHAddress:
    """Model for host/port combination."""

    host: str
    port: int


class StackzillaCompute(StackzillaResource):
    """Implementation for a compute provider."""

    @abstractmethod
    def ssh_credentials(self) -> SSHCredentials:
        """Provide the credentials needed to SSH into a host."""

    @abstractmethod
    def ssh_address(self) -> SSHAddress:
        """Provide the hostname/ip and port number for connecting to a host."""

    @abstractmethod
    def start(self, wait_for_online: True) -> None:
        """Called by Stackzilla when a compute resource needs to be started.

        Args:
            wait_for_online (True): If True, the function should wait for the compute to be online.

        Raises:
            ComputeStartError: Raised if there was an error starting the compute
        """

    @abstractmethod
    def stop(self, wait_for_offline: True) -> None:
        """Called by Stackzilla when a compute resourdce needs to be stopped.

        Args:
            wait_for_offline (True): Wait for the compute to stop.

        Raises:
            ComputeStopError: Raised if there was an error stopping the compute
        """

    def ssh_connect(self, retry_count: int=3, retry_delay: int=5) -> SSHClient:
        """Connect to the server via SSH.

        Returns:
            SSHClient: A Paralell-SSH client object
        """
        addr: SSHAddress = self.ssh_address()
        credentials: SSHCredentials = self.ssh_credentials()
        self._core_logger.debug(message=f'Connecting to {addr.host}', extra={'host': addr.host, 'port': addr.port})

        try:
            # If there's a key, use that!
            if credentials.key:
                client = SSHClient(host=addr.host, port=addr.port,
                               num_retries=retry_count, retry_delay=retry_delay,
                               pkey=credentials.key, user=credentials.username)
            else:
                client = SSHClient(host=addr.host, port=addr.port,
                                num_retries=retry_count, retry_delay=retry_delay,
                                password=credentials.password, user=credentials.username)

        except ConnectionRefusedError as err:
            raise SSHConnectError(str(err)) from err

        return client

    def wait_for_ssh(self, retry_count: int, retry_delay: int):
        """Wait for an SSH connection to become available.

        Args:
            retry_count (int): The number of times to try connecting
            retry_delay (int): The delay, in seconds, between connection attempts

        Raises:
            SSHConnectError: Raised when the connection fails to succeed after retrying
        """
        last_conn_err = None
        while retry_count >= 0:
            try:
                client = self.ssh_connect(retry_count=retry_count, retry_delay=retry_delay)
                client.disconnect()
                return
            except SSHConnectError as exc:
                retry_count -= 1
                self._core_logger.debug(f'Connection attempt failed: {str(exc)}')
                last_conn_err = exc

                # Wait for the specified delay before the next attempt
                if retry_count != 0:
                    time.sleep(retry_delay)

        raise last_conn_err
