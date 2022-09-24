# Blueprints

## Importer
The StackBot importer is a custom Python import hook. It recursively works through a single direcotry, importing
packages and modules as they're found. The `Importer` class contains all of this functionality and is consumed by the `Blueprint` class.

The `Importer` class contains event callbacks that are triggered when packages, modules, classes are found. The relevant callbacks are:
- `on_package_found`
- `on_module_found`
- `on_class_found`

### Class filter
StackBot only "cares" about classes within a blueprint which inherit from the base `StackBotResource`. Generally speaking, StackBot providers will inherit this base class, and in turn, those classes are then consumed by the end-user blueprint.

Example:
A blueprint has a webserver which inherits from the `CloudCompute` class from fictitious cloud vendor ACME. The `CloudCompute` class will inherit from the `StackBotResource` base class.

```python
from stackbot.providers.acme.compute import CloudCompute
class MyWebserver(CloudCompute):
    ...
```

Within the provider library:
```python
from stackbot.resource.base import StackBotResource
class CloudCompute(StackBotResource):
    ...
```

During import, StackBot will be able to detect that `MyWebserver` inhertis the `StackBotResource` class, via its consumption of the `CloudCompute` class.

### Relative Imports
Relative imports within the blueprint ARE allowed.
Example blueprint hierarchy:
```
/my_blueprint/
   /servers/
      /webserver.py
      /database.py
      /message_server.py
   /storage/
      /persistent_volumes.py
      /object_store.py
```

Within `webserver.py` it's perfecly valid to perform the following import statement:

```python
from .. storage.object_store import MyBucket
```