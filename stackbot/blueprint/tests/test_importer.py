"""Ensure that basic blueprint import functionality works."""
import logging
from pathlib import Path
from unittest.mock import Mock, patch

from stackbot.blueprint.importer import Importer

logger = logging.getLogger(__file__)

def test_single_file_import():
    """Import a blueprint with a single file"""
    test_bp = Path(__file__)
    fixture_location = test_bp.parent / 'fixtures' / 'single_file'

    importer = Importer(path=str(fixture_location), class_filter=object)

    with patch.object(importer, 'on_module_found', return_value=None) as mock_method:
        importer.load()
        importer.unload()

        assert mock_method.call_count == 1

def test_multiple_file_import():
    """Import a blueprint with multiple files in a single top-level directory"""

    test_bp = Path(__file__)
    fixture_location = test_bp.parent / 'fixtures' / 'multiple_files'

    importer = Importer(path=str(fixture_location), class_filter=object)

    with patch.object(importer, 'on_module_found', return_value=None) as mock_method:
        importer.load()
        importer.unload()

    assert mock_method.call_count == 3

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
