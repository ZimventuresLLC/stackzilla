"""Import modules from disk."""
import os
import pkgutil
from importlib import import_module
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import List, Optional, Type

from stackzilla.importer.base import BaseImporter, ModuleInfo


class Importer(BaseImporter):
    """Class to manage the import of an entire directory on disk."""

    def __init__(self, path: str, class_filter: Type[object] = None, package_root: Optional[str] = ''):
        """Initialize parameters and insert this class into the Python meta_path.

        Args:
            path (str): The filesystem path to the top level directory to be imported.
            class_filter (Type[object], optional): Only import classes inerhiting from this class. Defaults to None.
            package_root (Optional[str]): Sandbox the imported modules into a package root defined by this name. defaults to ''
        """
        super().__init__(class_filter=class_filter, package_root=package_root)

        self.bp_path: str = path
        self.current_file_path: Path = self.bp_path

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

    def _walk_packages(self, file_path):
        for (module_loader, name, is_pkg) in pkgutil.walk_packages(path=[file_path]):

            self.current_file_path = module_loader.path

            if is_pkg:
                self._logger.debug(f'Found package: {name} | {file_path = }')

                package = import_module(name=f'.{name}', package=self.current_python_path)

                package_name: str = package.__name__

                # If a package root is in use, strip it off before inserting it into the package cache
                if self._package_root:
                    package_name = package_name.replace(self._package_root, '.')

                self._packages[package_name] = package
                self.on_package_found(package=package)

                self._current_python_path.append(name)

                # Recurse
                self._walk_packages(file_path=os.path.join(file_path, name))

                # Remove the last item in the python path
                self._current_python_path.pop()
            else:
                self._logger.debug(f'import_module(name=.{name}, package={self.current_python_path}) | {file_path = }')
                module = import_module(
                    name=f'.{name}',
                    package=self.current_python_path
                )

                module_name = module.__name__

                # If the package root is in use, replace it with '.' before using it as the cache index
                if self._package_root:
                    module_name = module_name.replace(self._package_root, '.')

                # Save off the module into the cache
                module_file_data = None
                with open(module.__file__, 'r', encoding='utf-8') as module_file:
                    module_file_data = module_file.read()

                self._modules[module_name] = ModuleInfo(path=module_name, module=module, data=module_file_data)
                self.on_module_found(module=module)

                # Fire off all of the on_class_found() callbacks
                self._trigger_on_class_found(module=module)

    def find_spec(self, name, path, _target=None):
        """Python import hook for checking if the package being imported can be handled."""
        self._logger.debug(f'find_spec({name = }, {path = }, {_target = })')
        module_spec = None

        # Figure out if the {path}.{name} maps to somewhere in the package
        if path:
            # Ignore Stackzilla internals and any providers
            if name.startswith('stackzilla.'):
                self._logger.debug(f'Skipping {name}')
                return None

            # We don't know how to handle this module
            if path is None and name != f'.{self._package_root}':
                return None

            # If the path is a list, it's holding a file path
            if isinstance(path, list):
                if path[0].startswith(self.bp_path) is False:
                    return None

            # Save this to use when setting __package__ during module initialization
            self._current_spec_path = path
            module_spec = ModuleSpec(name, self)

        path_on_disk = os.path.join(self.bp_path, f'{name}.py')
        if os.path.exists(path_on_disk):
            self._current_spec_path = path
            module_spec = ModuleSpec(f'{self._package_root}.{name}', self)
        if name == '.':
            self._current_spec_path = path
            module_spec = ModuleSpec(name, self)
        if name == self._package_root:
            self._current_spec_path = path
            module_spec = ModuleSpec(name, self)

        if module_spec is None:
            self._logger.debug(f'Module ({path_on_disk}) not found')

        return module_spec

    def create_module(self, _spec):
        """Create the default Python module by returning None."""
        self._logger.debug(f'create_module({_spec = })')


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
            module.__file__ = module_file_path

            self._logger.debug(f'Execing f{module_file_path} into module {module.__name__}')
            module_file_data = ''
            with open(module_file_path, mode='r', encoding="utf-8") as module_file:
                module_file_data = module_file.read()
                exec(module_file_data, module.__dict__) # pylint: disable=exec-used

        else:
            err_msg = f'exec_module()\n\t{module.__name__ = }\n\t{package_dir_path = }\n\t{module_file_path = }'
            self._logger.critical(err_msg)
