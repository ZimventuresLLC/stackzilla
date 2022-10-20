"""Import modules from disk."""
# pylint: disable=R0801
from importlib import import_module
from importlib.machinery import ModuleSpec
from typing import List, Optional, Type

from stackzilla.database.base import StackzillaDB
from stackzilla.importer.base import BaseImporter, ModuleInfo
from stackzilla.utils.string import removeprefix


class DatabaseImporter(BaseImporter):
    """Class to manage the import of a blueprint from the Stackzilla database."""

    def __init__(self, class_filter: Type[object] = None, package_root: Optional[str] = ''):
        """Initialize parameters and insert this class into the Python meta_path.

        Args:
            class_filter (Type[object], optional): Only import classes inerhiting from this class. Defaults to None.
            package_root (Optional[str]): Sandbox the imported modules into a package root defined by this name. defaults to ''
        """
        # List of modules that are available from the database.
        # Used as a cache for checking in find_spec()
        self._bp_modules: List[str] = []

        # List of packages that are available from the database.
        self._bp_packages: List[str] = []

        super().__init__(class_filter=class_filter, package_root=package_root)

    def load(self):
        """Import the blueprint from the database."""
        # Import the top level directory as a module
        if self._package_root != '':
            self._current_python_path.append(f'{self._package_root}')
        else:
            self._current_python_path.append('.')


        self._bp_packages: List[str] = StackzillaDB.db.get_blueprint_packages()
        self._bp_modules: List[str] = StackzillaDB.db.get_blueprint_modules()

        for module_name in self._bp_modules:

            # Do importy things
            module_path_components = module_name.split('.')

            # Filter out any empty strings
            module_path_components = list(filter(('').__ne__, module_path_components))

            if self._package_root:
                if len(module_path_components) == 1:
                    package_path = f"{self._package_root}"
                else:
                    package_path = f"{self._package_root}.{'.'.join(module_path_components[:-1])}"
            else:
                package_path = f".{'.'.join(module_path_components[:-1])}"

            module_path_to_import = f'.{module_path_components[-1]}'

            self._logger.debug(f'import_module(name={module_path_to_import}, package={package_path})')
            module = import_module(
                name=module_path_to_import,
                package=package_path
            )

            # Save off the module
            module_name = module.__name__

            # If the package root is in use, strip it off of the module path before using it as the cache index
            if self._package_root:
                module_name = removeprefix(string=module_name, prefix=f'{self._package_root}.')

            # Prepend '..' for the lookup
            module_lookup_name = module_name
            if module_name.startswith('..') is False:
                module_lookup_name = '..' + module_name

            module_file_data = StackzillaDB.db.get_blueprint_module(module_lookup_name)
            self._modules[module_lookup_name] = ModuleInfo(path=module_lookup_name, module=module, data=module_file_data)

            self.on_module_found(module=module)

            # Fire off all of the on_class_found() callbacks
            self._trigger_on_class_found(module=module)

        # Reset the current paths
        self._current_python_path: List[str] = []
        self._current_spec_path: str = ''

        self._loaded = True

    def find_spec(self, name, path, _target=None):
        """Python import hook for checking if the package being imported can be handled."""
        self._logger.debug(f'find_spec({name = }, {path = }, {_target = })')

        module_spec = None

        # Figure out if the {path}.{name} maps to somewhere in the package
        if path:
             # Ignore Stackzilla internals and any providers
            if name.startswith('stackzilla.'):
                return None

            # We don't know how to handle this module
            if path is None and name != f'.{self._package_root}':
                return None

            # If the path is a list, it's holding a file path. Since we only care about DB modules, skip it!
            if isinstance(path, list):
                return None

            # Save this to use when setting __package__ during module initialization
            self._current_spec_path = path
            module_spec = ModuleSpec(name, self)

        # Check if this is a package that is being imported
        if name in self._bp_packages:
            self._logger.debug(f'Package ({name}) found')
            self._current_spec_path = path
            module_spec = ModuleSpec(f'{self._package_root}.{name}', self)

        if name == '.':
            self._logger.debug('Package (.) not found')
            self._current_spec_path = path
            module_spec = ModuleSpec(name, self)

        if name == self._package_root:
            self._logger.debug(f'Package ({name}) not found')
            self._current_spec_path = path
            module_spec = ModuleSpec(name, self)

        if module_spec is None:
            self._logger.debug(f'Module ({name}) not found')

        return module_spec

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

        if module_name.startswith('..') is False:
            module_name = '..' + module_name

        # Test what type of resource this is (package or module)
        if module_name in self._bp_packages:
            # This is a package
            module.__path__ = module.__name__

            # Save the package to the cache
            package_name: str = module_name
            if self._package_root:
                package_name = removeprefix(string=package_name, prefix=f'{self._package_root}.')

            self._packages[package_name] = module
            self.on_package_found(package=module)

        elif module_name in self._bp_modules:

            # This is a module
            module.__package__ = self._current_spec_path

            self._logger.debug(f'Execing {module_name} into module {module.__name__}')
            module_file_data = StackzillaDB.db.get_blueprint_module(path=module_name)
            exec(module_file_data, module.__dict__) # pylint: disable=exec-used

        else:
            err_msg = f'exec_module()\n\t{module.__name__ = }\n\t{module_name = }'
            self._logger.critical(err_msg)
