"""Base importer class."""
import inspect
import sys
from abc import abstractmethod
from dataclasses import dataclass
from types import ModuleType
from typing import Dict, List, Optional, Type

from stackzilla.importer.exceptions import ClassNotFound
from stackzilla.logger.core import CoreLogger


@dataclass
class ModuleInfo:
    """Data structure to hold information about loaded modules."""

    path: str
    data: str
    module: ModuleType

# pylint: disable=too-many-instance-attributes
class BaseImporter:
    """Interface definition for concrete importer classes."""

    def __init__(self, class_filter: Type[object] = None, package_root: Optional[str] = ''):
        """Initialize parameters and insert this class into the Python meta_path.

        Args:
            class_filter (Type[object], optional): Only import classes inerhiting from this class. Defaults to None.
            package_root (Optional[str]): Sandbox the imported modules into a package root defined by this name. defaults to ''
        """
        self._loaded: bool = False
        self._current_python_path: List[str] = []
        self._current_spec_path: str = ''
        self._class_filter = class_filter
        self._logger: CoreLogger = CoreLogger('importer')

        self._packages = {}
        self._modules: Dict[ModuleInfo] = {}
        self._classes: Dict[str, Type[object]] = {}

        self._package_root = package_root # Used for custom package roots

        sys.meta_path.insert(0, self)

    def get_class(self, name: str) -> Type[object]:
        """Fetch a previously imported class from the cache.

        Args:
            name (str): Full python path to the desired class

        Raises:
            ClassNotFound: Raised when the specified class is not found in the cache

        Returns:
            Type[object]: The desired class
        """
        full_path = name
        if self._package_root != '':
            full_path = f'{self._package_root}.{name}'
        else:
            full_path = f'..{name}'
        try:
            return self._classes[full_path]
        except KeyError as exc:
            raise ClassNotFound(name) from exc

    def unload(self):
        """Delete all imported packages, modules, and classes."""
        for module_info in self._modules.values():
            self._logger.debug(f'Deleting module: {module_info.module.__name__}')
            del sys.modules[module_info.module.__spec__.name]
            del module_info.module

        self._modules = {}

        for package_name, package in self._packages.items():
            self._logger.debug(f'Deleting package: {package_name}')
            del sys.modules[package.__spec__.name]
            del package

        self._packages = {}

        for class_name, class_obj in self._classes.items():
            self._logger.debug(f'Deleting class: {class_name}')
            del class_obj

        self._classes = {}

        self._loaded = False

    def create_module(self, _spec):
        """Create the default Python module by returning None."""
        self._logger.debug(f'create_module({_spec = })')

    @abstractmethod
    def load(self):
        """Import the blueprint."""

    @property
    def loaded(self) -> bool:
        """Indicaes if the package has been loaded or unloaded."""
        return self._loaded

    @property
    def classes(self) -> Dict[str, Type[object]]:
        """Fetch a list of all the imported classes which matched any specified import filters."""
        return self._classes

    @property
    def modules(self) -> Dict[str, ModuleInfo]:
        """Fetch all of the modules that were loaded by the importer."""
        return self._modules

    @property
    def packages(self) -> Dict[str, ModuleInfo]:
        """Fetch all of the packages that were loaded by the importer."""
        return self._packages

    @property
    def current_python_path(self):
        """Fetch the current Python path that is being imported.

        Returns:
            str: The current Python path being imported
        """
        return '.'.join(self._current_python_path)

    def on_package_found(self, package: ModuleType):
        """Event handler invoked for each package found during import.

        Args:
            package (ModuleType): The package that was found during import
        """

    def on_module_found(self, module: ModuleType):
        """Event handler invoked for each module found during import.

        Args:
            module (ModuleType): The module that was found during import
        """

    def on_class_found(self, name: str, obj: Type[object]):
        """Event handler which is called for each class during import.

        Args:
            name (str): Name of the class
            obj (Type[object]): The class that was imported.
        """

    @abstractmethod
    def find_spec(self, name, path, _target=None):
        """Python import hook for checking if the package being imported can be handled."""

    @abstractmethod
    def exec_module(self, module):
        """Initialize packages and modules within an end-user blueprint."""

    def _trigger_on_class_found(self, module: ModuleType):
        """Fire off the on_class_found() callback for all classes found in a module."""
        # Inform anyone that cares, a class was found.
        for obj_name, obj in inspect.getmembers(module, inspect.isclass):
            if self._class_filter is None or issubclass(obj, self._class_filter):

                # If the module is a stackzilla internal, ignore it
                skip = False
                for ignore_module in ['stackzilla.provider', 'stackzilla.resource']:
                    if obj.__module__.startswith(ignore_module):
                        skip = True
                        break

                if skip is False:
                    self._classes[f'{obj.__module__}.{obj.__name__}'] = obj
                    self.on_class_found(name=obj_name, obj=obj)
