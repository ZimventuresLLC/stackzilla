"""Interface for the Host Services functionality."""
import re
from enum import Enum, auto
from typing import List

from stackzilla.host_services.groups import GroupManagement, HostGroup
from stackzilla.host_services.package_managers.base import PackageManager
from stackzilla.host_services.users import HostUser, UserManagement
from stackzilla.logger.core import CoreLogger
from stackzilla.utils.ssh import SSHClient


# pylint: disable=invalid-name
class ServiceManagerType(Enum):
    """Enum to define the supported Linux service managers."""

    service = auto()
    systemctl = auto()

class HostServicesError(Exception):
    """Raised when a host services operation fails."""

# pylint: disable=too-many-instance-attributes
class HostServices:
    """Interface for working with a remote operating system."""

    def __init__(self, ssh_client: SSHClient) -> None:
        """Default constructor."""
        self._client: SSHClient = ssh_client
        self._is_posix: bool = False
        self._linux_distro: str = '<unknown>'
        self._logger: CoreLogger = CoreLogger(component='host-services')
        self._os: str = '<unknown>'
        self._package_managers = []
        self._os_version: str = ''
        self._service_manager = None

        # Gather information about the host system.
        self._query_system_facts()

    @property
    def os_name(self) -> str:
        """Get the OS string."""
        return self._os

    @property
    def os_version(self) -> str:
        """Get the Operating System version."""
        return self._os_version

    @property
    def is_posix(self) -> bool:
        """Return a boolean indicating if the system is POSIX based."""
        return self._is_posix

    @property
    def linux_distro(self) -> str:
        """Return the name of the Linux distribution."""
        return self._linux_distro

    @property
    def service_manager(self) -> str:
        """Fetch the service manager to use."""
        return self._service_manager.name

    @property
    def package_managers(self) -> List[PackageManager]:
        """Fetch a list of the package managers on the system."""
        return self._package_managers

    def create_users(self, users: List[HostUser]) -> None:
        """Create users on the remote host."""
        user_mgmt = UserManagement(self._client, self.linux_distro)
        user_mgmt.create_users(users=users)

    def delete_users(self, users: List[HostUser]) -> None:
        """Delete users on the remote host."""
        user_mgmt = UserManagement(ssh_client=self._client, distro=self.linux_distro)
        user_mgmt.delete_users(users=users)

    def create_groups(self, groups: List[HostGroup]) -> None:
        """Create groups on the remote host."""
        group_mgmt = GroupManagement(ssh_client=self._client, distro=self.linux_distro)
        group_mgmt.create_groups(groups=groups)

    def delete_groups(self, groups: List[HostGroup]) -> None:
        """Delete gropus on the remote host."""
        group_mgmt = GroupManagement(ssh_client=self._client, distro=self.linux_distro)
        group_mgmt.delete_groups(groups=groups)

    def add_authorized_ssh_key(self, user: str, key: str) -> None:
        """Add a new SSH key to the list of authorized keys.

        Args:
            user (str): Name of the user the key is being added for
            key (str): The public portion of the SSH key
        """
        output = self._client.run_command(command=f'echo "{key}" >> /home/{user}/.ssh.authorized_keys')
        if output.exit_code:
            raise HostServicesError(output.stderr)

    def remove_authorized_ssh_key(self, user: str, key: str) -> None:
        """Delete a key from the users list of authorized SSH keys.

        Args:
            user (str): The user to delete the key for
            key (str): The public portion of the SSH key
        """
        output = self._client.run_command(command=f'sed -i "\\:{key}:d" /home/{user}/.ssh/authorized_keys')
        if output.exit_code:
            raise HostServicesError(output.stderr)

    def restart_service(self, service: str) -> None:
        """Restart a service using the configured service manager.

        Args:
            service (str): Name of the service to restart

        Raises:
            RuntimeError: Raised if an unsupported service manager is encountered
            HostServicesError: Raised if the operation fails
        """
        if self._service_manager == ServiceManagerType.service:
            cmd = f'service {service} restart'
        elif self._service_manager == ServiceManagerType.systemctl:
            cmd = f'systemctl restart {service}'
        else:
            raise RuntimeError('Unsupported service manager encountered.')

        output= self._client.run_command(command=cmd, sudo=True)
        if output.exit_code:
            raise HostServicesError(output.stderr)

    def start_service(self, service: str) -> None:
        """Start/enable a service using the configured service manager.

        Args:
            service (str): Name of the service to start

        Raises:
            RuntimeError: Raised if an unsupported service manager is encountered
            HostServicesError: Raised if the operation fails
        """
        if self._service_manager == ServiceManagerType.service:
            cmd = f'service {service} start'
        elif self._service_manager == ServiceManagerType.systemctl:
            cmd = f'systemctl enable --now {service}'
        else:
            raise RuntimeError('Unsupported service manager encountered.')

        output = self._client.run_command(command=cmd, sudo=True)
        if output.exit_code:
            raise HostServicesError(output.stderr)

    def stop_service(self, service: str) -> None:
        """Stop/disable a service using the configured service manager.

        Args:
            service (str): Name of the service to stop

        Raises:
            RuntimeError: Raised if an unsupported service manager is encountered
            HostServicesError: Raised if the operation fails
        """
        if self._service_manager == ServiceManagerType.service:
            cmd = f'service {service} stop'
        elif self._service_manager == ServiceManagerType.systemctl:
            cmd = f'systemctl disable --now {service}'
        else:
            raise RuntimeError('Unsupported service manager encountered.')

        output = self._client.run_command(command=cmd, sudo=True)
        if output.exit_code:
            raise HostServicesError(output.stderr)

    def _query_system_facts(self):
        """Determine the remote OS type, package manager, and other details."""
        self._logger.debug(f'Starting host services fact check for {self._client.host}')

        # First thing first - determine if this is a POSIX-based operating system
        output = self._client.run_command(command='uname')
        if output.exit_code == 0:
            self._is_posix = True
            self._logger.debug(f'uname output: {output.stderr} | Uname exit-code {output.exit_code}')
        else:
            # This is not a posix-based system
            self._logger.debug(f'uname exited with {output.exit_code}')

        # Save off the output from uname.
        # This will be "Linux" for Linux based systems[]
        self._os = output.stdout.strip()

        # Now it's time to determine the distribution that is installated.
        output = self._client.run_command(command='cat /etc/os-release')

        if output.exit_code == 0:
            self._logger.debug(f'Contents of /etc/os-release: {output.stdout}')

            # There is a line that starts with "ID=" which has the distro name.
            matches = re.findall(r'^ID=(.*)$', output.stdout, re.MULTILINE)
            if matches:
                self._linux_distro = matches[0].strip()

                # Remove any quotes around the distro name
                self._linux_distro = self._linux_distro.strip('"')

                self._logger.debug(f'Distro found: {self._linux_distro}')

            # if "VERSION_ID" is in the output, that is the distro version
            matches = re.findall(r'VERSION_ID=(.*)$', output.stdout, re.MULTILINE)
            if matches:
                self._os_version = matches[0].strip()

                # Remove any quotes around the version
                self._os_version = self._os_version.strip('"')

                self._logger.debug(f'Distro version found: {self._os_version}')
        else:
            self._logger.debug('/etc/os-release file was not found')

        # Determine which package managers are present
        for mgr in PackageManager.suppported_managers():
            if mgr.exists(ssh_client=self._client):
                self._package_managers.append(mgr(self._client))

        # Run a secondary os version check if one wasn't found in /etc/os-release
        if self._os_version is None:
            self._get_os_version()

        # Determine which service manager is installed. The first one found, wins.
        for mgr in [ServiceManagerType.service, ServiceManagerType.systemctl]:
            output = self._client.run_command(command=f'which {mgr.name}')
            if output.exit_code == 0:
                self._service_manager = mgr
                break

    def _get_os_version(self):
        """Fetch the operating system version."""
        if self._linux_distro == "amzn":
            # Amazon Linux stores the version in /etc/os-release.
            output = self._client.run_command(command='cat /etc/os-release')

            if output.exit_code == 0:
                match = re.search(r'VERSION=\"([0-9]+)\"', output.stdout)
                if match:
                    self._os_version = match.group(1)

        elif self._linux_distro == "centos":
            # Centos stores its version information in /etc/centos-release
            output = self._client.run_command(command='cat /etc/centos-release')
            if output.exit_code == 0:
                match = re.search(r'CentOS Linux release ([0-9]+\.[0-9+])"', output.stdout)
                if match:
                    self._os_version = match.group(1)

        elif self._linux_distro == "rhel":
            output = self._client.run_command(command='cat /etc/os-release')
            matches = re.findall(r'^VERSION_ID=(.*)', output.stdout, re.MULTILINE)
            if matches:
                self._os_version = matches[0].strip().rstrip('\r').strip('"')

        elif self._linux_distro == "ubuntu":
            output = self._client.run_command(command='cat /etc/os-release')
            if output.exit_code == 0:
                match = re.search(r'VERSION_ID=\"(.*)\"', output.stdout)
                if match:
                    self._os_version = match.group(1)
