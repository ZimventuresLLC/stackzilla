"""Module for managing host system users."""
from dataclasses import dataclass
from typing import List

from stackzilla.host_services.exceptions import UnsupportedPlatform
from stackzilla.logger.core import CoreLogger
from stackzilla.utils.ssh import SSHClient


@dataclass
class HostUser:
    """Model for a system user."""

    name: str
    # Optional attributes
    extra_groups: str = None
    group: str = None
    home_dir: str = None
    id: int = None          # pylint: disable=invalid-name
    password: str = None
    shell: str = None

class UserCreateError(Exception):
    """Raised when the user creation fails."""

class UserDeleteError(Exception):
    """Raised when the user deletion fails."""

class UserManagement:
    """Interface for performing user management on a host."""

    def __init__(self, ssh_client: SSHClient, distro: str) -> None:
        """Constructor for the UserManagement class."""
        self._client: SSHClient = ssh_client
        self._distro: str = distro
        self._logger: CoreLogger = CoreLogger(component='user-mgmt')

    def create_users(self, users: List[HostUser]):
        """Create the users on the host system."""
        if self._distro == 'amzn':
            self._create_amzn_users(users=users)
        elif self._distro == 'alpine':
            self._create_alpine_users(users=users)
        elif self._distro in ['centos', 'debian', 'fedora', 'gentoo', 'opensuse-leap', 'rhel', 'slackware', 'ubuntu']:
            self._create_standard_users(users=users)
        else:
            self._logger.critical('Unsupported platform detected in create_users', extra={'distro': self._distro})
            raise UnsupportedPlatform(self._distro)

    def delete_users(self, users: List[HostUser]):
        """Delete users from the remote host."""
        if self._distro == 'amzn':
            self._delete_amazon_users(users=users)
        elif self._distro in ['alpline', 'ubuntu']:
            self._delete_alpine_ubuntu_users(users=users)
        elif self._distro in ['centos', 'debian', 'fedora', 'gentoo', 'rhel', 'slackware', 'opensuse-leap']:
            self._delete_users(users=users)
        else:
            self._logger.critical('Unsupported platform detected in delete_users', extra={'distro': self._distro})
            raise UnsupportedPlatform(self._distro)

    def _create_amzn_users(self, users: List[HostUser]):
        """Build up and execute the CLI command to create the list of users."""
        for user in users:
            cmd = 'sudo useradd '

            if user.home_dir:
                cmd += f' -d {user.home_dir}'

            if user.shell:
                cmd += f' -s {user.shell}'

            if user.id:
                cmd += f' -u {user.id}'

            if user.group:
                cmd += f' -g {user.group}'

            if user.extra_groups:
                cmd += f' -G {user.extra_groups}'

            cmd += f' {user.name}'

            self._logger.debug(f'Creating user {user.name} on an Amazon Linux host')
            output = self._client.run_command(command=cmd)

            if output.exit_code:
                raise UserCreateError(output.stderr)

            if user.password:
                output = self._client.run_command(command=f'sudo su -c "echo {user.name}:{user.password} | chpasswd"')
                if output.exit_code:
                    self._logger.critical(f'User creation failed: {output.stderr}')
                    raise UserCreateError(output.stderr)

    def _create_alpine_users(self, users: List[HostUser]):
        """Create a list of users on an Alpine-based host."""
        for user in users:
            cmd = 'adduser -D'

            if user.home_dir:
                cmd += f' -h {user.home_dir}'

            if user.shell:
                cmd += f' -s {user.shell}'

            if user.id:
                cmd += f' -u {user.id}'

            if user.group:
                cmd += f' -g {user.group}'

            if user.extra_groups:
                cmd += f' -G {user.extra_groups}'
            cmd += f' {user.name}'

            output = self._client.run_command(command=cmd)
            if output.exit_code:
                raise UserCreateError(output.stderr)

            if user.password:
                output = self._client.run_command(command=f'echo "{user.name}:{user.password}" | chpasswd', sudo=True)
                if output.exit_code:
                    raise UserCreateError(output.stderr)

    def _create_standard_users(self, users: List[HostUser]):
        """Creates users via the 'useradd' CLI tool. Works on most Linux distros."""
        for user in users:
            cmd = 'sudo useradd '

            if user.home_dir:
                cmd += f' -d {user.home_dir}'
            if user.shell:
                cmd += f' -s {user.shell}'
            if user.id:
                cmd += f' -u {user.id}'
            if user.group:
                cmd += f' -g {user.group}'
            if user.extra_groups:
                cmd += f' -G {user.extra_groups}'

            cmd += f' {user.name}'

            output = self._client.run_command(command=cmd)
            if output.exit_code:
                raise UserCreateError(output.stderr)

            if user.password:
                output = self._client.run_command(command=f'echo "{user.name}:{user.password}" | chpasswd', sudo=True)
                if output.exit_code:
                    raise UserCreateError(output.stderr)

    def _delete_amazon_users(self, users: List[HostUser]):
        """Delete users from an Amazon Linux host."""
        for user in users:
            output = self._client.run_command(command=f'userdel {user.name}', sudo=True)
            if output.exit_code:
                raise UserDeleteError(output.stderr)

    def _delete_alpine_ubuntu_users(self, users: List[HostUser]):
        """Delete users from an Alpline host."""
        for user in users:
            output = self._client.run_command(command=f'deluser {user.name}', sudo=True)
            if output.exit_code:
                raise UserDeleteError(output.stderr)

    def _delete_users(self, users: List[HostUser]):
        """Delete users from a Linux distro using the 'userdel' CLI command."""
        for user in users:
            output = self._client.run_command(command=f'userdel {user.name}', sudo=True)
            if output.exit_code:
                raise UserDeleteError(output.stderr)
