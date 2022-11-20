"""Helper module for reading data of the HostOutput stdout buffer."""
from typing import Tuple
from pssh.output import HostOutput

def read_output(output: HostOutput) -> Tuple[str, int]:
    """Helper method to iterate over a stdout generator from pssh"""
    stdout = ''
    for line in output.stdout:
        stdout += f"{line}\n"

    return (stdout, output.exit_code)
