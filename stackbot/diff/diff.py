"""Module that has all of the logic for diffing imported blueprints."""
from dataclasses import dataclass
from enum import Enum
from stackbot.database.base import StackBotDB
from stackbot.resource import StackBotResource

class DiffResult(Enum):
    SAME = 1
    CONFLICT = 2
    REBUILD_REQUIRED = 3

@dataclass
class AttributeDiff:
    pass



class ResourceDiff:
    """Compute the differences between two collection of modules."""

    def __init__(self) -> None:
        pass

    def compare(self, resource: StackBotResource):

        db_resource = StackBotDB.db.get_resource(path=resource.path())

        # TODO: Check the resource version against the database

        # Check 
        for attribute in resource.attributes: