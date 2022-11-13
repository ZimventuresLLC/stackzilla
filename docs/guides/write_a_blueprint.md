---
permalink: /write-a-blueprint/
layout: home
title: Write A Blueprint
---

# Write A Blueprint
In this guide, you'll learn how to create a Stackzilla **Blueprint**. By the end of the guide, your blueprint will provision an SSH key, a server, and an extra block-storage volume that will be attached to the server.


## Install dependencies
For this tutorial we'll be using the [Linode](linode.com) provider. Let's start by making sure Stackzilla Core and the Linode provider are both installed. It is assumed that you are performing module installation in a *virtual environment* and not on the base system. You're doing that...right? 🧐

```bash
$ pip install -U stackzilla
$ pip install -U stackzilla-provider-linode
```
## Blueprint setup
Create a new directory `my_bp` and within it, create the file `__init__.py`.

{% capture verify_note %}
Every directory in your blueprint, including the root directory, is considered a Python module. As such, it is <b>REQUIRED</b> that each directory has a <code>__init__.py</code> file. If the file is missing, Stackzilla will skip importing it, and any sub-modules within.
{% endcapture %}
{% include note-warning.html content=verify_note %}


## A Single Module
It's time to get coding! Open a new file, `volume.py`. This file will have a single class, `MyVolume`, with attributes that will determine how our volume is created. Here's what the final class will look like:

```python
import os
from stackzilla.provider.linode.volume import LinodeVolume

# Set the API token required by the provider
LinodeVolume.token = os.getenv('STACKZILLA_LINODE_TOKEN')

class MyVolume(LinodeVolume):
    def __init__(self):
        super().__init__()
        self.size = 60
        self.region = 'us-east'
        self.tags = ['foo', 'bar', 'zim']
        self.label = 'Stackzilla_Testing'
```

Let's start from the top!

```python
import os
from stackzilla.provider.linode.volume import LinodeVolume
```

All Stackzilla providers are imported from the `stackzilla.provider.` namespace. See your provider's documentation for more details.

```python
LinodeVolume.token = os.getenv('STACKZILLA_LINODE_TOKEN')
```
This is specific to the Linode providers. In order for the provider to interact with the Linode API, a secret key is required. We set that key by storing it in the environment variable `STACKZILLA_LINODE_TOKEN` but you can store and retrieve this key however works best for your workflow.

```python
class MyVolume(LinodeVolume):
```

Your resource will *inherit* from the provider class. Doing so exposes it to Stackzilla at runtime.

```python
def __init__(self):
    super().__init__()
```

Your blueprint resources are customized by the attributes defined within them. Attribures are defined in the **constructor** for the resource. That means your resource attributes are *instance variables*.

{% capture constructor_note %}
Be sure to play nice and call the base classes constructor *before* performing any initialization. You never know if a base class has initialization logic that is required for it to function properly.
{% endcapture %}
{% include note-warning.html content=constructor_note %}

```python
    self.size = 60
    self.region = 'us-east'
    self.tags = ['foo', 'bar', 'zim']
    self.label = 'Stackzilla_Testing'
```

Attributes are provider-specific. Some attributs are *required* and blueprint verification will fail if they are not declared. For the Linode volume, the `size` (in gigabytes), `region` (where it is hosted), and `label` (name shown in the UI) are required. The `tags` attribute is optional, but we've specified it for illustrative purposes.

### Try it out
With the blueprint definition complete, let's try having Stackzilla use it!

Create a new test namespace:
```bash
$ stackzilla --namespace test init
```

Apply the blueprint:
```bash
$ stackzilla --namespace test blueprint apply --path ./my_bp/
[volume.MyVolume] CREATING
++      filesystem_path: <none> => <TBD>
++      instance: <none> => ..instance.MyServer
++      label: <none> => Stackzilla_Testing_2
++      region: <none> => us-east
++      size: <none> => 60
++      tags: <none> => ['foo', 'bar', 'zim']
++      volume_id: <none> => <TBD>

Apply Changes? [y/N]:
```

After answering "y" to the question, the blueprint should be applliled, and your volume should now be available on Linode. Navigate to the [Volume Page](https://cloud.linode.com/volumes) and verify that is the case!

## Blueprint Modification
The initial deployment of a blueprint is just the start of the party! What if, after deployment, we want to increase the size of the volume. *No problem*.

Update the blueprint so that the `size` attribute from `60` to `120`.

```python
class MyVolume(LinodeVolume):
    def __init__(self):
        super().__init__()

        self.size = 120
        # ...
```

Apply the blueprint and review the diff that is printed to the screen:
```bash
$ stackzilla --namespace test blueprint apply --path ./my_bp/
[volume.MyVolume] UPDATING
@@      size: 60 => 120

Apply Changes? [y/N]: y
2022-11-13 16:42:00,170 (INFO:linode.volume) Updating volume size from 60 to 120
$
```

### Modify Rebuild
Some attributes, when modified, will require the resource to be deleted and then recreated. Take, for example, the case where the volume's region is changed. Linode does not support migration of the volume, so it. must be deleted and created again. Let's try that out.

Update the region to `us-west`
```python
    self.region = 'us-west'
```

Run `blueprint apply`.
```bash
$ stackzilla --namespace test blueprint apply --path ./my_bp/
[volume.MyVolume] REBUILD REQUIRED. See attributes marked with "!!"
!!      region: us-east => us-west

Apply Changes? [y/N]:  y
2022-11-13 16:49:06,780 (DEBUG:linode.volume) Deleting Stackzilla_Testing_2
2022-11-13 16:49:07,389 (DEBUG:linode.volume) Deletion complete
2022-11-13 16:49:07,389 (DEBUG:linode.volume) Starting volume creation Stackzilla_Testing_2
2022-11-13 16:49:07,774 (INFO:linode.volume) Volume creation complete: 637102
$
```

As you can see from the logs, the volume is deleted and recreated in the new region. The console output, is very explicit that a rebuild is required. Pay attention to this before applying your blueprint!

## Blueprint Deletion
Before continuing on with the tutorial, let's delete the blueprint from the first section. In order to delete the entire blueprint, invoke the `blueprint delete` command.

```bash
$ stackzilla --namespace test blueprint delete
Delete blueprint? [y/N]:
```
After answering "y", the blueprint will be deleted, and your resources will be too.

## Multiple Modules
Single module blueprints are handy, but more complex environments and applications will need multiple modules. To illustrate this, let's create a blueprint with two modules: `server.py` and `key.py`.

### `key.py`
The first module (`key.py`) will define an SSH key via the `MyKey` class.

```python
from stackzilla.resource.ssh_key import StackzillaSSHKey

class MyKey(StackzillaSSHKey):
    def __init__(self) -> None:
        super().__init__()
        self.key_size = 2048
```

### `server.py`
Our server will reference the `MyKey` class with a *relative import*. We'll talk more about relative imports a little further in this gude.

```python
import os
from stackzilla.provider.linode.instance import LinodeInstance

from .key import MyKey

LinodeInstance.token = os.getenv('STACKZILLA_LINODE_TOKEN')

class MyServer(LinodeInstance):
    def __init__(self):
        super().__init__()
        self.region = 'us-east'
        self.type = 'g6-nanode-1'
        self.image = 'linode/alpine3.12'
        self.label = 'Stackzilla_Test-Linode.1'
        self.tags = ['testing']
        self.private_ip = False
        self.ssh_key = MyKey
```

## Directories
Blueprints can have sub-directories in them for a cleaner hierarchy of resources. All subdirectories must have an `__init__.py` in order for Stackzilla to import them at runtime.

### Relative Imports
When using multiple direcotries for a blueprint, it is likely that resrouces from different modules will need to depend each other. Relative imports, to the rescue!

Given the following blueprint toplogy:
```
./key.py
./servers/
  - primary.py
  - backup.py
./load_balancer/
  - alb.py
```

Let's say the servers defined in `./servers/primary.py`  and `./servers/backup.py` want to access a key defined in `./key.py`.

Here is how that is accomplished:

```python
from .key import MyKey
```

The root of the blueprint (`./my_bp`) is the root of relative imports. Navigating to other levels of the blueprint is also possible using multiple path separators. An example of that would be importing a server from `primary.py` within the `alb.py` module.

```python
from ..server.primary import MyPrimaryServer
```
