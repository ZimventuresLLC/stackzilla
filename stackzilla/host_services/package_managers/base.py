"""Base interface for all Stackzilla supported package managers."""
from abc import abstractmethod
from typing import List, Type

from stackzilla.logger.core import CoreLogger
from stackzilla.utils.ssh import SSHClient


class InstallError(Exception):
    """Raised when a package installation fails."""

class UninstallError(Exception):
    """Raised when a package uninstall fails."""

class PackageManager:
    """Base package manager class."""

    def __init__(self, ssh_client: SSHClient) -> None:
        """Default construcor. Saves off SSH client."""
        self.client: SSHClient = ssh_client
        self.logger: CoreLogger = CoreLogger(component='package-manager')

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
    def uninstall_packages(self, packages: List[str]) -> None:
        """Invoked when it's time to delete packages."""

    @staticmethod
    def suppported_managers() -> List[Type['PackageManager']]:
        """Fetch a list of all the package manager classes."""
        return [APK, APT, YUM, Emerge, InstallPKG]

class APK(PackageManager):
    """Apline Package Keeper. Not quite as cool as a Trapper Keeper."""

    @classmethod
    def name(cls) -> str:
        """Fetch the name of the package manager."""
        return "apk"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if APK is present on the system."""
        output = ssh_client.run_command(command='which apk')
        return output.exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using APK."""
        package_list = ' '.join(packages)
        cmd = f'apk add --no-progress {package_list}'
        self.logger.debug(message=cmd)
        output = self.client.run_command(command=cmd)
        if output.exit_code:
            raise InstallError(output.stderr)

    def uninstall_packages(self, packages: List[str]) -> None:
        """Uninstall packages using APK."""
        package_list = ' '.join(packages)
        cmd = f'apk del --no-progress {package_list}'
        self.logger.debug(message=cmd)
        output = self.client.run_command(command=cmd)
        if output.exit_code:
            raise UninstallError(output.stderr)

class APT(PackageManager):
    """Advanced Packaging Tool."""

    @classmethod
    def name(cls) -> str:
        """Fetch the name of the package manager."""
        return "apt"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if APT is present on the system."""
        output = ssh_client.run_command(command='which apt')
        return output.exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using APT."""
        # Update the package manager first...
        self.logger.debug('Updating apt')
        output = self.client.run_command('apt update', sudo=True)
        if output.exit_code:
            self.logger.critical(f'apt update failed: {output.stderr}')
            raise InstallError(output.stderr)

        package_list = ' '.join(packages)
        cmd = f'apt install -y {package_list}'
        self.logger.debug(message=cmd)
        output = self.client.run_command(command=cmd, sudo=True)
        if output.exit_code:
            self.logger.critical(f'apt install failed: {output.stderr}')
            raise InstallError(output.stderr)

    def uninstall_packages(self, packages: List[str]) -> None:
        """Uninstall packages using APT."""
        package_list = ' '.join(packages)
        cmd = f'apt remove -y {package_list}'
        self.logger.debug(message=cmd)
        output = self.client.run_command(command=cmd, sudo=True)
        if output.exit_code:
            self.logger.critical(f'apt remove failed with: {output.stderr}')
            raise UninstallError(output.stderr)

class YUM(PackageManager):
    """Yellowdog Updater, Modified (YUM)."""

    @classmethod
    def name(cls) -> str:
        """Fetch the name of the package manager."""
        return "yum"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if YUM is present on the system."""
        output = ssh_client.run_command(command='which yum')
        return output.exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using YUM."""
        package_list = ' '.join(packages)
        cmd = f'yum install -y {package_list}'
        self.logger.debug(message=cmd)
        output = self.client.run_command(command=cmd, sudo=True)
        if output.exit_code:
            combined = output.stderr + output.stderr
            self.logger.critical(f'yum install failed: {combined}')
            raise InstallError(combined)

    def uninstall_packages(self, packages: List[str]) -> None:
        """Uninstall packages using YUM."""
        package_list = ' '.join(packages)
        cmd = f'yum remove -y {package_list}'
        self.logger.debug(message=cmd)
        output = self.client.run_command(command=cmd, sudo=True)
        if output.exit_code:
            combined = output.stderr + output.stderr
            raise UninstallError(combined)

class Emerge(PackageManager):
    """CLI interface for Portage (the Gentoo package manager)."""

    @classmethod
    def name(cls) -> str:
        """Fetch the name of the package manager."""
        return "emerge"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if Emerge is present on the system."""
        output = ssh_client.run_command(command='which emerge')
        return output.exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using Emerge."""
        package_list = ' '.join(packages)
        cmd = f'emerge --nospinner --quiet-build y {package_list}'
        self.logger.debug(message=cmd)
        output = self.client.run_command(command=cmd)
        if output.exit_code:
            self.logger.critical(f'emerge failed with: {output.stderr}')
            raise InstallError(output.stderr)

    def uninstall_packages(self, packages: List[str]) -> None:
        """Uninstall packages using Emerge."""
        package_list = ' '.join(packages)
        cmd = f'emerge --deselect {package_list}'
        self.logger.debug(message=cmd)
        output = self.client.run_command(command=cmd)
        if output.exit_code:
            self.logger.critical(f'emerge failed with: {output.stderr}')
            raise UninstallError(output.stderr)

class InstallPKG(PackageManager):
    """CLI interface for Portage (the Gentoo package manager)."""

    @classmethod
    def name(cls) -> str:
        """Fetch the name of the package manager."""
        return "installpkg"

    @classmethod
    def exists(cls, ssh_client: SSHClient) -> bool:
        """Check if installpkg is present on the system."""
        output = ssh_client.run_command(command='which installpkg')
        return output.exit_code == 0

    def install_packages(self, packages: List[str]) -> None:
        """Install packages using upgradepkg."""
        # First, dowload all of the packages to /tmp
        package_list = ''
        for pkg in packages:
            self.logger.debug(f'Downloading {pkg} to /tmp')
            output = self.client.run_command(f'cd /tmp; wget {pkg}')
            if output.exit_code:
                self.logger.critical(f'Download failed with: {output.stderr}')
                raise InstallError(output.stderr)

            # Build a list of package names that we'll send to the upgradepkg command
            package_url = pkg[1]
            package_list += f'{package_url.split("/")[-1]} '

        self.logger.debug(f'Installing {package_list}')
        output = self.client.run_command(f'cd /tmp; upgradepkg --install-new {package_list}')
        if output.exit_code:
            self.logger.critical(f'Install failed with: {output.stderr}')
            raise InstallError(output.stderr)

    def uninstall_packages(self, packages: List[str]) -> None:
        """Uninstall packages using removepkg."""
        package_list = ''
        for pkg in packages:
            # Build a list of package names that we'll send to the upgradepkg command
            package_url = pkg[1]
            packages_list += f'{package_url.split("/")[-1]} '

        self.logger.debug(f'Uninstalling {package_list}')
        output = self.client.run_command(f'cd /tmp; ugpradepkg --install-new {package_list}')
        if output.exit_code:
            self.logger.critical(f'Uninstall failed with: {output.stderr}')
            raise UninstallError(output.stderr)
