"""Module for generation and management of RSA keys which are subsequently used for SSH."""
from typing import List

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from stackzilla.attribute import StackzillaAttribute
from stackzilla.logger.provider import ProviderLogger
from stackzilla.resource.base import ResourceVersion, StackzillaResource


class StackzillaSSHKey(StackzillaResource):
    """Interface for generation of an OpenSSH compatible RSA key."""

    key_size: int = StackzillaAttribute(default=2048, types=[int])
    private_key: bytes = StackzillaAttribute(dynamic=True, secret=True)
    public_key: bytes = StackzillaAttribute(dynamic=True)


    def __init__(self) -> None:
        """Constructor. Sets up logging."""
        super().__init__()
        self._logger = ProviderLogger(provider_name='stackzilla.ssh-key', resource_name=self.path())

    def create(self) -> None:
        """Create a new key which can be used for SSH."""
        self._logger.debug(f'Starting RSA Key generation. {self.key_size =}')

        key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=self.key_size
        )

        self.private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        self.public_key = key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )

        self._logger.debug('Key generation and OpenSSH export complete.')

        # Save the results to the dataase
        super().create()

    def depends_on(self) -> List['StackzillaResource']:
        """No dependencies."""
        return []

    @classmethod
    def version(cls) -> ResourceVersion:
        """Fetch the version of the resource provider."""
        return ResourceVersion(major=0, minor=1, build=0, name='alpha')
