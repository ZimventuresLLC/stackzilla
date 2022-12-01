"""Verify that multi-threaded database access works."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
from typing import List
from uuid import UUID, uuid4

from stackzilla.attribute import StackzillaAttribute
from stackzilla.database.sqlite import StackzillaSQLiteDB
from stackzilla.resource import ResourceVersion, StackzillaResource

resources = []
class Resource(StackzillaResource):
    """Demo resource."""
    uuid: UUID = StackzillaAttribute(required=True)
    required = StackzillaAttribute(required=True)
    default_int = StackzillaAttribute(required=False, default=42)
    list_attr = StackzillaAttribute(required=False)
    dict_attr = StackzillaAttribute(required=False)

    @classmethod
    def version(cls) -> ResourceVersion:
        return ResourceVersion(major=1, minor=0, build=0, name='FCS')

def db_write_worker(database: StackzillaSQLiteDB, range: List[int]):
    """Dynamically create resource classes and add them to the database."""
    for index in range:
        new_class = type(f'MyResource{index}', (Resource,), {})
        globals()[f'MyResource{index}'] = new_class
        my_resource = new_class()
        my_resource.uuid = uuid4()
        resources.append(my_resource)
        database.create_resource(resource=my_resource)

        # Give the other threads a chance to play
        sleep(0.01)


def db_read_worker(database: StackzillaSQLiteDB, cycles: int):
    """Helper function which read all resources from the database."""
    for _ in range(cycles):
        # Give the other threads a chance to play
        sleep(0.01)
        database.get_all_resources()

def test_multiple_writes(database: StackzillaSQLiteDB):
    """Write multiple objects to the database at the same time."""
    futures = []
    with ThreadPoolExecutor() as executor:
        futures.append(executor.submit(db_write_worker, database=database, range=range(0, 10, 1)))
        futures.append(executor.submit(db_write_worker, database=database, range=range(10, 20, 1)))
        futures.append(executor.submit(db_write_worker, database=database, range=range(20, 30, 1)))

    for result in as_completed(futures):
        assert result.exception() is None
        assert result.result() is None

    # Make sure all of the resources made it into the database
    assert len(database.get_all_resources()) == 30

    # Iterate over each resource and ensure they can be queried by path
    for index in range(0, 30, 1):
        resource_name = f'database.tests.test_concurrency.MyResource{index}'
        database.get_resource(path=resource_name)

def test_multi_read_write(database: StackzillaSQLiteDB):
    """Verify that reading and writing to the database at the same time works."""
    futures = []
    with ThreadPoolExecutor(max_workers=16) as executor:
        # Create a bunch of resources
        futures.append(executor.submit(db_write_worker, database=database, range=range(0, 50, 1)))

        # While simultaneously reading everything from the database over and over
        print('starting read')
        futures.append(executor.submit(db_read_worker, database=database, cycles=50))

    for result in as_completed(futures):
        assert result.exception() is None
        assert result.result() is None
