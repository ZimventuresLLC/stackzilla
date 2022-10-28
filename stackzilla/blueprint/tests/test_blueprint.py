"""Ensure that blueprints work as expected using the NULL provider."""
import logging
from pathlib import Path
from stackzilla.blueprint import StackzillaBlueprint


logger = logging.getLogger(__file__)

def test_basic():
    """Verify that loading a blueprint from disk and verifying it works."""
    test_bp = Path(__file__)
    fixture_location = test_bp.parent / 'fixtures' / 'ha_webapp'

    # Import the blueprint from disk and verify it
    disk_blueprint = StackzillaBlueprint(path=str(fixture_location))
    disk_blueprint.load()
    disk_blueprint.verify()
