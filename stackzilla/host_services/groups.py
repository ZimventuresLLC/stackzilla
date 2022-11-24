"""Functionality for creating and managing groups on a remote system."""
from dataclasses import dataclass
from typing import List

from stackzilla.host_services.exceptions import UnsupportedPlatform
from stackzilla.logger.core import CoreLogger
from stackzilla.utils.ssh import SSHClient


@dataclass
class HostGroup:
    """Simple model which represents a host group."""

    name: str
    id: int = None # pylint: disable=invalid-name

class GroupCreateFailure(Exception):
    """Raised when the group creation process fails."""

class GroupDeleteFailure(Exception):
    """Raised when the group deletion process fails."""

class GroupManagement:
    """Interface for group management."""

    def __init__(self, ssh_client: SSHClient, distro: str) -> None:
        """Constructor for the UserManagement class."""
        self._client: SSHClient = ssh_client
        self._distro: str = distro
        self._logger: CoreLogger = CoreLogger(component='group-mgmt')

    # pylint: disable=too-many-branches
    def create_groups(self, groups: List[HostGroup]):
        """Create groups on the remote host.

        Args:
            groups (List[HostGroup]): The groups to create

        Raises:
            GroupCreateFailure: Raised if any of the create operations fails
        """
        if self._distro == 'amzn':
            base_cmd = 'groupadd'
            for group in groups:
                if group.id:
                    cmd = f'{base_cmd} --gid {group.id} {group.name}'
                else:
                    cmd = f'{base_cmd} {group.name}'

                self._logger.debug(f'Creating group: {cmd}')
                output = self._client.run_command(command=cmd, sudo=True)

                if output.exit_code:
                    raise GroupCreateFailure(output.stderr)

        else:
            # These distros have differences in the group id command
            for group in groups:
                if group.id:
                    if self._distro == 'alpline':
                        cmd = f'addgroup -g {group.id} {group.name}'
                    elif self._distro in ['centos', 'debian', 'fedora', 'gentoo', 'opensuse-leap', 'rhel', 'slackware']:
                        cmd = f'groupadd --gid {group.id} {group.name}'
                    elif self._distro == 'ubuntu':
                        cmd = f'addgroup --gid {group.id} {group.name}'
                    else:
                        self._logger.critical('Unsupported platform detected in create_groups', extra={'distro': self._distro})
                        raise UnsupportedPlatform(self._distro)
                else:
                    if self._distro in['alpine', 'ubuntu']:
                        cmd = f'addgroup {group.name}'
                    elif self._distro in ['centos', 'debian', 'fedora', 'gentoo', 'opensuse-leap', 'rhel', 'slackware']:
                        cmd = f'groupadd {group.name}'
                    else:
                        self._logger.critical('Unsupported platform detected in create_groups', extra={'distro': self._distro})
                        raise UnsupportedPlatform(self._distro)

                self._logger.debug(f'Creating new group {group.name}')
                output = self._client.run_command(command=cmd, sudo=True)

                if output.exit_code:
                    raise GroupCreateFailure(output.stderr)

    def delete_groups(self, groups: List[HostGroup]):
        """Delete the specified groups on the remote host.

        Args:
            groups (List[HostGroup]): The groups to delete
        """
        for group in groups:

            if self._distro in ['alpline', 'ubuntu']:
                cmd = f'delgroup {group.name}'
            elif self._distro in ['amzn', 'centos', 'debian', 'fedora', 'gentoo', 'opensuse-leap', 'rhel', 'slackware']:
                cmd = f'groupdel {group.name}'
            else:
                self._logger.critical('Unsupported platform detected in delete_groups', extra={'distro': self._distro})
                raise UnsupportedPlatform(self._distro)

            self._logger.debug(message=f'Deleting group: {group.name}')
            output = self._client.run_command(command=cmd, sudo=True)

            if output.exit_code:
                raise GroupDeleteFailure(output.stderr)
