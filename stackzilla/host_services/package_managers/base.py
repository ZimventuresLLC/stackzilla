"""Base interface for all Stackzilla supported package managers."""
from abc import abstractmethod
from typing import List, Type

from pssh.clients import SSHClient
from pssh.output import HostOutput

from stackzilla.utils.ssh import read_output

class PackageManager:
    """Base package manager class."""

    def __init__(self, ssh_client: SSHClient) -> None:
        """Default construcor. Saves off SSH client."""
        self.client: SSHClient = ssh_client

    @classmethod
    def name(cls) -> str:
        """Get the name of the package manager."""
        return 'Unknown'

    @classmethod
    @abstractmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Called when Stackzilla wants to check if the package manager exists on the host system."""

    @abstractmethod
    def install_packages(self, packages: List[str]) -> None:
        """Stackzilla will invoke this when it wants to install packages."""

    @abstractmethod
    def uninstall_packaegs(self, packages: List[str]) -> None:
        """Invoked when it's time to delete packages."""

    @staticmethod
    def suppported_managers() -> List[Type['PackageManager']]:
        """Fetch a list of all the package manager classes."""
        return [APK, APT, YUM, Emerge, InstallPKG]

class APK(PackageManager):
    """Apline Package Keeper. Not quite as cool as a Trapper Keeper. 😎"""

    @classmethod
    def name(cls) -> str:
        return "apk"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if APK is present on the system."""
        output: HostOutput = ssh_client.run_command(command='which apk')
        _, exit_code = read_output(output)
        return exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using APK."""
        package_list = ' '.join(packages)
        self.client.run_command(f'apk add --no-progress {package_list}')

    def uninstall_packaegs(self, packages: List[str]) -> None:
        """Uninstall packages using APK."""
        package_list = ' '.join(packages)
        self.client.run_command(f'apk del --no-progress {package_list}')

class APT(PackageManager):
    """Advanced Packaging Tool."""

    @classmethod
    def name(cls) -> str:
        return "apt"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if APT is present on the system."""
        output: HostOutput = ssh_client.run_command(command='which apt')
        _, exit_code = read_output(output)
        return exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using APT."""
        package_list = ' '.join(packages)
        self.client.run_command(f'apt install -y {package_list}', sudo=True)

    def uninstall_packaegs(self, packages: List[str]) -> None:
        """Uninstall packages using APT."""
        package_list = ' '.join(packages)
        self.client.run_command(f'apt remove -y {package_list}', sudo=True)

class YUM(PackageManager):
    """Yellowdog Updater, Modified (YUM)"""

    @classmethod
    def name(cls) -> str:
        return "yum"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if YUM is present on the system."""
        output: HostOutput = ssh_client.run_command(command='which yum')
        _, exit_code = read_output(output)
        return exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using YUM."""
        package_list = ' '.join(packages)
        self.client.run_command(f'yum install -y {package_list}', sudo=True)

    def uninstall_packaegs(self, packages: List[str]) -> None:
        """Uninstall packages using YUM."""
        package_list = ' '.join(packages)
        self.client.run_command(f'yum remove -y {package_list}', sudo=True)

class Emerge(PackageManager):
    """CLI interface for Portage (the Gentoo package manager)."""

    @classmethod
    def name(cls) -> str:
        return "emerge"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if Emerge is present on the system."""
        output: HostOutput = ssh_client.run_command(command='which emerge')
        _, exit_code = read_output(output)
        return exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using Emerge."""
        package_list = ' '.join(packages)
        self.client.run_command(f'emerge --nospinner --quiet-build y {package_list}')

    def uninstall_packaegs(self, packages: List[str]) -> None:
        """Uninstall packages using Emerge."""
        package_list = ' '.join(packages)
        self.client.run_command(f'emerge --deselect {package_list}')

class InstallPKG(PackageManager):
    """CLI interface for Portage (the Gentoo package manager)."""

    @classmethod
    def name(cls) -> str:
        return "installpkg"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if installpkg is present on the system."""
        output: HostOutput = ssh_client.run_command(command='which installpkg')
        _, exit_code = read_output(output)
        return exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using upgradepkg."""

        # First, dowload all of the packages to /tmp
        package_list = ''
        for pkg in packages:
            self.client.run_command(f'cd /tmp; wget {pkg}')

            # Build a list of package names that we'll send to the upgradepkg command
            package_url = pkg[1]
            package_list += f'{package_url.split("/")[-1]} '

        self.client.run_command(f'cd /tmp; upgradepkg --install-new {package_list}')

    def uninstall_packaegs(self, packages: List[str]) -> None:
        """Uninstall packages using removepkg."""
        package_list = ''
        for pkg in packages:
            # Build a list of package names that we'll send to the upgradepkg command
            package_url = pkg[1]
            packages_list += f'{package_url.split("/")[-1]} '

        self.client.run_command(f'cd /tmp; ugpradepkg --install-new {package_list}')
