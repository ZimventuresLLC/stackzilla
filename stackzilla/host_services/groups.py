"""Functionality for creating and managing groups on a remote system."""
from dataclasses import dataclass
from typing import List

from pssh.clients import SSHClient
from pssh.output import HostOutput

from stackzilla.logger.core import CoreLogger
from stackzilla.utils.ssh import read_output


@dataclass
class HostGroup:
    """Simple model which represents a host group."""

    name: str
    id: int = None # pylint: disable=invalid-name

class GroupCreateFailure(Exception):
    """Raised when the group creation process fails."""

class GroupDeleteFailure(Exception):
    """Raised when the group deletion process fails."""

class UnsupportedPlatform(Exception):
    """Raised if an unsupported platform is detected."""

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
            cmd = 'groupadd'
            for group in groups:
                if group.id:
                    cmd = f'{cmd} --gid {group.id} {group.name}'
                else:
                    cmd = f'{cmd} {group.name}'

            output: HostOutput = self._client.run_command(command=cmd, sudo=True)
            stdout, exit_cmd = read_output(output)

            if exit_cmd:
                raise GroupCreateFailure(stdout)

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
                        raise UnsupportedPlatform(self._distro)
                else:
                    if self._distro in['alpine', 'ubuntu']:
                        cmd = f'addgroup {group.name}'
                    elif self._distro in ['centos', 'debian', 'fedora', 'gentoo', 'opensuse-leap', 'rhel', 'slackware']:
                        cmd = f'groupadd {group.name}'
                    else:
                        raise UnsupportedPlatform()

                self._logger.debug(f'Creating new group {group.name}')
                output: HostOutput = self._client.run_command(command=cmd, sudo=True)
                stdout, exit_code = read_output(output)

                if exit_code:
                    raise GroupCreateFailure(stdout)

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
                raise UnsupportedPlatform()

            self._logger.debug(message=f'Deleting group: {group.name}')
            output: HostOutput = self._client.run_command(command=cmd, sudo=True)
            stdout, exit_cmd = read_output(output)

            if exit_cmd:
                raise GroupDeleteFailure(stdout)
