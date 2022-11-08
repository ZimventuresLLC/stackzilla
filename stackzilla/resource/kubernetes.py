"""Interface definition for Kubernetes Providers on Stackzilla."""
from abc import abstractmethod
from typing import List

from stackzilla.resource.base import StackzillaResource


class StackzillaKubernetes(StackzillaResource):
    """Abstract interface defintion for a Stackzilla Kubernetes provider."""

    @abstractmethod
    def get_certificate_data(self) -> str:
        """Fetch the certificate data for accessing the cluster."""

    @abstractmethod
    def get_kubeconfig(self) -> str:
        """Build and return a kubeconfig that can be used to access the cluster."""

    @abstractmethod
    def get_endpoint(self) -> str:
        """Get the URL used for connecting to the cluster."""

    @abstractmethod
    def get_nodes(self) -> List[List[str]]:
        """Fetch a mapping of all the node information. Implementaiton specific."""
