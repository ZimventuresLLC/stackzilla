"""Helper module for SSH."""
from dataclasses import dataclass
from typing import Optional

from pssh.clients.ssh import SSHClient as PSSHClient
from pssh.output import HostOutput


@dataclass
class CmdResult:
    """Results of a SSHClient.run_command() operation."""

    stdout: str
    exit_code: int
    stderr: Optional[str] = None

class SSHClient:
    """Wrapper class around Parallell SSH."""

    def __init__(self, client: PSSHClient):
        """Basic constructor."""
        self._client = client

    def run_command(self, command: str, sudo: bool=False, use_pty=False) -> CmdResult:
        """Execute a command on the remote host.

        Args:
            command (str): The command to execute
            sudo (bool, optional): Execute the command with elevated priveleges. Defaults to False.
            use_pty (bool, optional): Use a pseudo terminal. Defaults to False.

        Returns:
            Tuple[str, int]: The STDOUT for the command and the exit code
        """
        output: HostOutput = self._client.run_command(command=command, sudo=sudo, use_pty=use_pty)
        self._client.wait_finished(output)

        exit_code = output.exit_code
        stdout = ''
        for line in output.stdout:
            stdout += f'{line}\n'

        stderr = ''
        result = CmdResult(stdout=stdout, exit_code=exit_code)

        # If there is any error output, grab it
        if output.stderr:
            for line in output.stderr:
                stderr += f'{line}\n'

            result.stderr = stderr

        return result

    def disconnect(self):
        """Disconnect the client."""
        self._client.disconnect()

    @property
    def host(self):
        """Fetch the host address of the current connection."""
        return self._client.host
