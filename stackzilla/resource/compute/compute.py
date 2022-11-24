"""Module for base compute functionality."""
import time
from abc import abstractmethod
from dataclasses import dataclass
from typing import List

from pssh.clients.ssh import SSHClient as PSSHClient
from pssh.exceptions import AuthenticationError

from stackzilla.attribute import StackzillaAttribute
from stackzilla.host_services import HostServices
from stackzilla.host_services.groups import HostGroup
from stackzilla.host_services.users import HostUser
from stackzilla.resource.base import StackzillaResource
from stackzilla.resource.compute.exceptions import (NoPackageManagers,
                                                    SSHConnectError)
from stackzilla.utils.ssh import SSHClient


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

    # Optional attributes
    groups = StackzillaAttribute(required=False)
    users = StackzillaAttribute(required=False)
    packages = StackzillaAttribute(required=False)

    def __init__(self) -> None:
        """Constructor for the compute class."""
        super().__init__()

        # Attach a handler for when the instance is done being created
        self.on_create_done.attach(handler=self._on_create_done)

    def _on_create_done(self, sender: StackzillaResource): # pylint: disable=unused-argument
        """Event handler for when the compute creation is complete.

        Args:
            sender (StackzillaResource): Sender of the event
        """
        if self.users or self.groups or self.packages:
            ssh_client = self.ssh_connect()
            host_service = HostServices(ssh_client=ssh_client)

            if self.groups:
                host_service.create_groups(groups=self.groups)

            if self.users:
                host_service.create_users(users=self.users)

            if self.packages:
                if len(host_service.package_managers) == 0:
                    raise NoPackageManagers('No package managers available')

                pkg_mgr = host_service.package_managers[0]
                pkg_mgr.install_packages(packages=self.packages)

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


    def restart_service(self, service: str) -> None:
        """Restart a service running on the system.

        Args:
            service (str): Name of the service to restart.
        """
        client = self.ssh_connect()
        host_services = HostServices(ssh_client=client)
        host_services.restart_service(service=service)

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
                client = PSSHClient(host=addr.host, port=addr.port,
                                    num_retries=retry_count, retry_delay=retry_delay,
                                    pkey=credentials.key, user=credentials.username)
            else:
                client = PSSHClient(host=addr.host, port=addr.port,
                                    num_retries=retry_count, retry_delay=retry_delay,
                                    password=credentials.password, user=credentials.username)

        except AuthenticationError as err:
            raise SSHConnectError(f'Authentication failed: {str(err)}') from err
        except ConnectionRefusedError as err:
            raise SSHConnectError(f'Connection error: {str(err)}') from err

        return SSHClient(client=client)

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

    def users_modified(self, previous_value: List[HostUser], new_value: List[HostUser]):
        """Handle the modification of the users parameter."""
        client = self.ssh_connect()
        host_services = HostServices(ssh_client=client)

        # Delete any users
        users_to_delete = []
        if previous_value:
            for user in previous_value:

                # Check for the presence of the username in the old list of users.
                if new_value is None or user.name not in [old_user.name for old_user in new_value]:
                    users_to_delete.append(user)

            if users_to_delete:
                host_services.delete_users(users=users_to_delete)

        # Create new users
        users_to_create = []
        if new_value:
            for user in new_value:
                if previous_value is None or user.name not in [new_user.name for new_user in previous_value]:
                    users_to_create.append(user)

            if users_to_create:
                host_services.create_users(users=users_to_create)

    def groups_modified(self, previous_value: List[HostGroup], new_value: List[HostGroup]):
        """Handle the modification of the groups parameter."""
        client = self.ssh_connect()
        host_services = HostServices(ssh_client=client)

        # Delete any groups
        groups_to_delete = []
        if previous_value:
            for group in previous_value:
                if new_value is None or group not in new_value:
                    groups_to_delete.append(group)

        if groups_to_delete:
            host_services.delete_groups(groups=groups_to_delete)

        # Create new groups
        groups_to_create = []
        if new_value:
            for group in new_value:
                if previous_value is None or group not in previous_value:
                    groups_to_create.append(group)

        if groups_to_create:
            host_services.create_groups(groups=groups_to_create)

    def packages_modified(self, previous_value: List[str], new_value: List[str]):
        """Handle when the list of packages is updated."""
        client = self.ssh_connect()
        host_services = HostServices(ssh_client=client)
        pkg_mgr = host_services.package_managers[0]

        # First pass will delete any packages that were removed from the host
        packages_to_delete = []
        if previous_value:
            for package in previous_value:
                if new_value is None or package not in new_value:
                    packages_to_delete.append(package)

        if packages_to_delete:
            pkg_mgr.uninstall_packages(packages=packages_to_delete)

        # Add any new packages
        packages_to_add = []
        if new_value:
            for package in new_value:
                if previous_value is None or package not in previous_value:
                    packages_to_add.append(package)

        if packages_to_add:
            pkg_mgr.install_packages(packages=packages_to_add)
