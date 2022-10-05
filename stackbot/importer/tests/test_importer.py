"""Ensure that basic blueprint import functionality works."""
import logging
from pathlib import Path
from unittest.mock import Mock

import pytest

from stackbot.importer.exceptions import ClassNotFound
from stackbot.importer.importer import Importer

logger = logging.getLogger(__file__)

def test_single_file_import():
    """Import a blueprint with a single file"""
    test_bp = Path(__file__)
    fixture_location = test_bp.parent / 'fixtures' / 'single_file'

    importer = Importer(path=str(fixture_location), class_filter=None)

    importer.on_module_found = Mock()
    importer.on_class_found = Mock()

    importer.load()

    importer.get_class(name='fileA.ResourceA')

    importer.unload()

    assert importer.on_class_found.call_count == 2
    assert importer.on_module_found.call_count == 1

def test_reload():
    """Verify that unloading and re-loading a package works."""
    test_bp = Path(__file__)
    fixture_location = test_bp.parent / 'fixtures' / 'multiple_files'

    importer = Importer(path=str(fixture_location), class_filter=object)
    importer.load()
    assert importer.classes
    importer.unload()
    assert not importer.classes
    importer.load()
    assert importer.classes
    importer.unload()
    assert not importer.classes

def test_multiple_file_import():
    """Import a blueprint with multiple files in a single top-level directory"""

    test_bp = Path(__file__)
    fixture_location = test_bp.parent / 'fixtures' / 'multiple_files'

    importer = Importer(path=str(fixture_location), class_filter=object)

    importer.on_module_found = Mock()
    importer.on_class_found = Mock()

    importer.load()

    # Verify that all of the classes are fetchable
    for class_name in ['fileA.ResourceA', 'fileA.ResourceAA', 'fileB.ResourceB', 'fileB.ResourceBB', 'fileC.ResourceC']:
        importer.get_class(name=class_name)

    importer.unload()

    # Verify that all of the classes have been unloaded
    for class_name in ['fileA.ResourceA', 'fileA.ResourceAA', 'fileB.ResourceB', 'fileB.ResourceBB', 'fileC.ResourceC']:
        with pytest.raises(ClassNotFound):
            importer.get_class(name=class_name)

    assert importer.on_class_found.call_count == 6
    assert importer.on_module_found.call_count == 3

def test_multi_layer_import():
    """Import a blueprint with multiple sub-directories and files in each"""

    test_bp = Path(__file__)
    fixture_location = test_bp.parent / 'fixtures' / 'multiple_directories'

    importer = Importer(path=str(fixture_location), class_filter=object)

    importer.on_module_found = Mock()
    importer.on_package_found = Mock()
    importer.load()
    importer.unload()

    assert importer.on_module_found.call_count == 4
    assert importer.on_package_found.call_count == 2

def test_package_root():
    """Import a directory into a specific package root."""
    test_bp = Path(__file__)
    fixture_location = test_bp.parent / 'fixtures' / 'multiple_directories'

    importer = Importer(path=str(fixture_location), class_filter=object, package_root='testing')
    importer.on_module_found = Mock()
    importer.on_package_found = Mock()
    importer.load()
    importer.unload()

    assert importer.on_module_found.call_count == 4
    assert importer.on_package_found.call_count == 2

def test_multiple_package_roots():
    """Ensure that the same directory can be imported into multple package roots."""
    test_bp = Path(__file__)
    fixture_location = test_bp.parent / 'fixtures' / 'multiple_directories'

    importers = []
    for root in ['primary', 'secondary']:
        importer = Importer(path=str(fixture_location), class_filter=object, package_root=root)

        # Save the importer to a list so we can unload the modules after
        importers.append(importer)

        importer.on_module_found = Mock()
        importer.on_package_found = Mock()
        importer.load()

        assert importer.on_module_found.call_count == 4
        assert importer.on_package_found.call_count == 2

    # Make sure that all of the expected classes exist in both importers
    for importer in importers:
        for class_name in ['root_module.Root', 'root_module.MyThing', 'other_root_module.OtherRoot', 'a.a.A', 'b.b.B', 'b.b.CoolRoot']:
            importer.get_class(name=class_name)

    for importer in importers:
        importer.unload()