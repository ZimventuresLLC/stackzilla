"""Import modules from disk."""
from dataclasses import dataclass
from genericpath import isfile
import inspect
import os
import pkgutil
import sys
from importlib import import_module
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import List, Optional, Type

from stackbot.blueprint.exceptions import ClassNotFound
from stackbot.logging.core import CoreLogger

@dataclass
class ModuleInfo:
    """Data structure to hold information about loaded modules"""
    path: str
    data: str
    module: ModuleType


class Importer:
    """Class to manage the import of an entire directory on disk."""

    def __init__(self, path: str, class_filter: Type[object] = None, package_root: Optional[str] = ''):
        """Initialize parameters and insert this class into the Python meta_path.

        Args:
            path (str): The filesystem path to the top level directory to be imported.
            class_filter (Type[object], optional): Only import classes inerhiting from this class. Defaults to None.
            package_root (Optional[str]): Sandbox the imported modules into a package root defined by this name. defaults to ''
        """
        self._loaded: bool = False
        self.bp_path: str = path
        self.current_file_path: Path = self.bp_path
        self._current_python_path: List[str] = []
        self._current_spec_path: str = ''
        self._class_filter = class_filter
        self._logger: CoreLogger = CoreLogger('importer')

        self._packages = {}
        self._modules: dict[ModuleInfo] = {}
        self._classes: dict[str, Type[object]] = {}

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

    def load(self):
        """Import the blueprint previously specified in the constructor."""
        # Import the top level directory as a module

        if self._package_root != '':
            self._current_python_path.append(f'{self._package_root}')
        else:
            self._current_python_path.append('.')

        self._walk_packages(file_path=self.bp_path)

        # Reset the current paths
        self.current_file_path: Path = self.bp_path
        self._current_python_path: List[str] = []
        self._current_spec_path: str = ''

        self._loaded = True

    @property
    def loaded(self) -> bool:
        """Indicaes if the package has been loaded or unloaded."""
        return self._loaded

    @property
    def classes(self) -> dict[str, Type[object]]:
        """Fetch a list of all the imported classes which matched any specified import filters."""
        return self._classes

    @property
    def modules(self) -> dict[str, ModuleInfo]:
        """Fetch all of the modules that were loaded by the importer."""
        return self._modules

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

    def _walk_packages(self, file_path):
        for (module_loader, name, is_pkg) in pkgutil.walk_packages(path=[file_path]):

            self.current_file_path = module_loader.path

            if is_pkg:
                self._logger.debug(f'Found package: {name} | {file_path = }')

                package = import_module(name=f'.{name}', package=self.current_python_path)
                self._packages[package.__name__] = package
                self.on_package_found(package=package)

                self._current_python_path.append(name)

                # Recurse
                self._walk_packages(file_path=os.path.join(file_path, name))

                # Remove the last item in the python path
                self._current_python_path.pop()
            else:
                self._logger.debug(f'Found module: {name} | {file_path = } | {self.current_python_path =}')
                module = import_module(
                    name=f'.{name}',
                    package=self.current_python_path
                )

                self.on_module_found(module=module)

                # Inform anyone that cares, a class was found.
                for obj_name, obj in inspect.getmembers(module, inspect.isclass):
                    if self._class_filter is None or issubclass(obj, self._class_filter):

                        # If the module starts with 'stackbot.provider', ignore it
                        if obj.__module__.startswith('stackbot.provider'):
                            continue

                        self._classes[f'{obj.__module__}.{obj.__name__}'] = obj
                        self.on_class_found(name=obj_name, obj=obj)

    def find_spec(self, name, path, _target=None):
        """Python import hook for checking if the package being imported can be handled."""
        self._logger.debug(f'find_spec({name = }, {path = }, {_target = })')

        # Figure out if the {path}.{name} maps to somewhere in the package

        if path:
            pass
        else:
            path_on_disk = os.path.join(self.bp_path, f'{name}.py')
            if os.path.exists(path_on_disk):
                self._current_spec_path = path
                return ModuleSpec(f'{self._package_root}.{name}', self)
            elif name == '.':
                self._current_spec_path = path
                return ModuleSpec(name, self)
            elif name == self._package_root:
                self._current_spec_path = path
                return ModuleSpec(name, self)
            else:
                self._logger.debug(f'Module ({path_on_disk}) not found')
                return None

        # Ignore StackBot internals and any providers
        if name.startswith('stackbot.'):
            return None

        # We don't know how to handle this module
        if path is None and name != f'.{self._package_root}':
            return None

        # Save this to use when setting __package__ during module initialization

        self._current_spec_path = path
        return ModuleSpec(name, self)

    def create_module(self, _spec):
        """Create the default Python module by returning None."""
        self._logger.debug(f'create_module({_spec = })')
        return None

    def exec_module(self, module):
        """Initialize packages and modules within an end-user blueprint."""
        # Special case for the root package
        if module.__name__ == f'{self._package_root}':
            module.__path__ = f'{self._package_root}'
            return

        # If the package root is being used as a prefix, remove it before trying
        # to convert the python path into a file system path.
        module_name = module.__name__
        if self._package_root != '':
            if module_name.startswith(f'{self._package_root}.'):
                module_name = module_name.split(f'{self._package_root}.')[1]

        # Strip out the leading namespace, plus any path separators
        # Convert the module python path to a file system path (a.a.a -> a/a/a)
        if module_name.startswith('..'):
            # This is a top level subpackage
            module_file_path = module_name[2:].replace('.', os.path.sep)
        elif module_name.startswith('.'):
            # This is a top level module
            module_file_path = module_name[1:].replace('.', os.path.sep)
        else:
            module_file_path = module_name.replace('.', os.path.sep)

        package_dir_path= os.path.join(self.bp_path, module_file_path)
        module_file_path = os.path.join(self.bp_path, f'{module_file_path}.py')

        if os.path.isdir(package_dir_path):
            # This is a package
            module.__path__ = module.__name__

        elif os.path.exists(module_file_path):

            # This is a module
            module.__package__ = self._current_spec_path

            self._logger.debug(f'Execing f{module_file_path} into module {module.__name__}')
            module_file_data = ''
            with open(module_file_path, mode='r', encoding="utf-8") as module_file:
                module_file_data = module_file.read()
                exec(module_file_data, module.__dict__) # pylint: disable=exec-used

            # Save off the module
            self._modules[module.__name__] = ModuleInfo(path=module.__name__, module=module, data=module_file_data)

        else:
            err_msg = f'exec_moudle()\n\t{module.__name__ = }\n\t{package_dir_path = }\n\t{module_file_path = }'
            self._logger.critical(err_msg)
