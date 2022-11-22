"""Interface for the Host Services functionality."""
import re
from typing import List

from pssh.clients import SSHClient
from pssh.output import HostOutput

from stackzilla.host_services.groups import GroupManagement, HostGroup
from stackzilla.host_services.package_managers.base import PackageManager
from stackzilla.host_services.users import HostUser, UserManagement
from stackzilla.logger.core import CoreLogger
from stackzilla.utils.ssh import read_output


class HostServicesError(Exception):
    """Raised when a host services operation fails."""
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
        stdout, exit_code = read_output(output)
        if exit_code:
            raise HostServicesError(stdout)

    def remove_authorized_ssh_key(self, user: str, key: str) -> None:
        """Delete a key from the users list of authorized SSH keys.

        Args:
            user (str): The user to delete the key for
            key (str): The public portion of the SSH key
        """
        output = self._client.run_command(command=f'sed -i "\\:{key}:d" /home/{user}/.ssh/authorized_keys')
        stdout, exit_code = read_output(output)
        if exit_code:
            raise HostServicesError(stdout)

    def _query_system_facts(self):
        """Determine the remote OS type, package manager, and other details."""
        self._logger.debug(f'Starting host services fact check for {self._client.host}')

        # First thing first - determine if this is a POSIX-based operating system
        output: HostOutput = self._client.run_command(command='uname')
        stdout, exit_code = read_output(output)
        if exit_code == 0:
            self._is_posix = True
            self._logger.debug(f'uname output: {stdout} | Uname exit-code {exit_code}')
        else:
            # This is not a posix-based system
            self._logger.debug(f'uname exited with {output.exit_code}')

        # Save off the output from uname.
        # This will be "Linux" for Linux based systems[]
        self._os = stdout.strip()

        # Now it's time to determine the distribution that is installated.
        output: HostOutput = self._client.run_command(command='cat /etc/os-release', use_pty=True)
        stdout, exit_code = read_output(output)

        if exit_code == 0:
            self._logger.debug(f'Contents of /etc/os-release: {stdout}')

            # There is a line that starts with "ID=" which has the distro name.
            matches = re.findall(r'^ID=(.*)$', stdout, re.MULTILINE)
            if matches:
                self._linux_distro = matches[0].strip()

                # Remove any quotes around the distro name
                self._linux_distro = self._linux_distro.strip('"')

                self._logger.debug(f'Distro found: {self._linux_distro}')

            # if "VERSION_ID" is in the output, that is the distro version
            matches = re.findall(r'VERSION_ID=(.*)$', stdout, re.MULTILINE)
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

    def _get_os_version(self):
        """Fetch the operating system version."""
        if self._linux_distro == "amzn":
            # Amazon Linux stores the version in /etc/os-release.
            output: HostOutput = self._client.run_command(command='cat /etc/os-release')
            stdout, exit_code = read_output(output)

            if exit_code == 0:
                match = re.search(r'VERSION=\"([0-9]+)\"', stdout)
                if match:
                    self._os_version = match.group(1)

        elif self._linux_distro == "centos":
            # Centos stores its version information in /etc/centos-release
            output: HostOutput = self._client.run_command(command='cat /etc/centos-release')
            if output.exit_code == 0:
                match = re.search(r'CentOS Linux release ([0-9]+\.[0-9+])"', read_output(output.stdout))
                if match:
                    self._os_version = match.group(1)

        elif self._linux_distro == "rhel":
            output: HostOutput = self._client.run_command(command='cat /etc/os-release')
            matches = re.findall(r'^VERSION_ID=(.*)', read_output(output.stdout), re.MULTILINE)
            if matches:
                self._os_version = matches[0].strip().rstrip('\r').strip('"')

        elif self._linux_distro == "ubuntu":
            output: HostOutput = self._client.run_command(command='cat /etc/os-release')
            if output.exit_code == 0:
                match = re.search(r'VERSION_ID=\"(.*)\"', read_output(output.stdout))
                if match:
                    self._os_version = match.group(1)
