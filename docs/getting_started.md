---
permalink: /getting-started/
layout: home
title: Getting Started
---

# Welcome

Welcome to Stackzilla! You're about to take a programatic journey into *Application ORM bliss*.

Buckle up kids, let's ride. 🏎

# Install Stackzilla

Stackzilla is distributed via [PyPI](https://pypi.org/project/stackzilla/). Installing it is as easy as running `pip install stackzilla`.

Installing Stackzilla by iteself, while neccessary, doesn't get us far. Each resource that we're going provision needs a **provider** plugin to be installed. Let's do that next. 🔜

## Provider Installation
Like Stackzilla, providers can also be installed via `pip`. All provider modules will be prefixed with `stackzilla-provider-`. For this getting started guide, we'll be using an AWS provider.

```bash
$ pip install stackzilla-provider-aws
Defaulting to user installation because normal site-packages is not writeable
Collecting stackzilla-provider-aws
  Using cached stackzilla_provider_aws-0.1.3-py2.py3-none-any.whl (31 kB)

<... pip instlallation output ..>

Installing collected packages: stackzilla-provider-aws
Successfully installed stackzilla-provider-aws-0.1.3
$
```

# Usage
Developers interact with Stackzilla in two ways: by writing *blueprints* and using the Stackzilla CLI tool. Let's take a quick look at what a blueprint looks like. The example below defines an AWS EC2 instance with the supporting SSH key, and security group, which are both needed to connect to it.
## A simple blueprint

Create a new [Python module ](https://realpython.com/python-modules-packages/#python-modules-overview) by performing the following steps

```bash
mkdir my_blueprint
touch my_blueprint/__init__.py
```

Now in your favorite editor, create a new file in the `my_blueprint` directory with the name `my_blueprint.py`.

Time to get coding!

```python
from stackzilla.provider.aws.ec2.key_pair import AWSKeyPair
from stackzilla.provider.aws.ec2.instance import AWSInstance
from stackzilla.provider.aws.ec2.security_group import AWSSecurityGroup, AWSSecurityGroupRule, IPAddressRange

class MyKey(AWSKeyPair):
    """AWS Key Pair."""

    def __init__(self):
        super().__init__()
        self.name = 'my-ssh-key'
        self.region = 'us-east-1'

class AllowSSH(AWSSecurityGroup):
    """A security group that allows incoming SSH connections."""

    def __init__(self):
        super().__init__()

        self.ingress = [
            AWSSecurityGroupRule(cidr_blocks=[IPAddressRange('0.0.0.0/0', 'the whole wide world')],
                                 protocol='tcp', from_port=22, to_port=22)
        ]
        self.name = 'InboundSSH'
        self.description = 'Allows incoming TCP connections to port 22'
        self.region = 'us-east-1'


class MyServer(AWSInstance):
    """EC2 Instance."""

    def __init__(self):
        super().__init__()

        self.name = 'my-demo-server'
        self.region = 'us-east-1'
        self.type = 't2.micro'
        self.security_groups = [AllowSSH]
        self.ssh_key = MyKey
        self.ami = 'ami-0c4e4b4eb2e11d1d4'  # Amazon Linux 2 AMI
        self.ssh_username = 'ec2-user'
```

### Resources
Each `class` in the blueprint is defining a **resource**. You'll notice that in our example blueprint, each `class` inherits from a base. In the case of `MyServer`, it inherits from the `AWSInstance` base class. These base clases, defined by provider plugins, are where all of the logic resides to interact with what is being defined. `AWSInstance` "knows" how to provision, interact with, and manage AWS EC2 instances.

### Attributes
Stackzilla **resources** are built using **attributes**. **Attributes** are simply class member variables that have been defined by the underlying provider. It's the job of the blueprint author ( wake up, that's you!) to customize the attributes for your use case. For our demo blueprint, inside of `MyServer` the following attributes are defined:

- `name` - The display name of the EC2 instance, when viewed in the AWS console
- `region` - AWS Region the EC2 instance is to be created in
- `type` - Server class. We're using the `t2.micro` because it's free! (for a limited time)
- `security_groups` - ACL-style rules for network firewalling
- `ssh_key` - The RSA key used for SSH
- `ami` - ID of the image to install on the server. We're using Amazon Linux 2 for the demo
- `ssh_username` - Username to be used in tandem with the ssh_key for connecting to the host

**Attributes** are defined within the **resource** constructor: `__init__()`. Always be sure to call the base constructor, and set the attributes on the instnace by prefacing them with the "`self.`" scope.

## Stackzilla Namespaces
A Stackzilla **namespace** is a datastore for housing metadata about your blueprint, and things we've done with it. Under the hood, Stackzilla namespaces are simply SQLite databases. Treat the namespace files with caution as without them, Stackzilla will have no recollection of what you've done!

Let's create a namespace called "demo"

```bash
stackzilla --namespace demo init
```

This will create a local file named `demo.db`. The `--namespace` parameter will need to be specified to all future Stackzilla commands.

## Provisioning
With the blueprint and our namespace defined, it's time to move on to *provisioning*. Provisioning is the process of converting our blueprints into instantiated infrastructure. To perform provisioning, the `stackzilla blueprint apply` command will load in a blueprint, verify it, and then commence applying.

Applying is a process whereby the provided blueprint is compared against the last known state of the namespace. For the initial apply, there is no state, so everything will be created. In subsequent blueprint applications only the differences are applied.

```bash
stackzilla --namespace demo blueprint apply --path ./my_blueprint/

[my_blueprint.AllowSSH] CREATING
++      arn: <none> => <TBD>
++      description: <none> => Allows incoming TCP connections to port 22
++      egress: <none> => None
++      group_id: <none> => <TBD>
++      ingress: <none> => [AWSSecurityGroupRule(cidr_blocks=[IPAddressRange(cidr_block='0.0.0.0/0', description='the whole wide world')], from_port=22, protocol='tcp', source_group=None, to_port=22)]
++      name: <none> => InboundSSH
++      region: <none> => us-east-1
++      tags: <none> => None
++      vpc_id: <none> => None
[my_blueprint.MyKey] CREATING
++      arn: <none> => <TBD>
++      format: <none> => pem
++      key_fingerprint: <none> => <TBD>
++      key_material: <none> => <secret>
++      key_pair_id: <none> => <TBD>
++      name: <none> => my-ssh-key
++      region: <none> => us-east-1
++      tags: <none> => None
++      type: <none> => rsa
[my_blueprint.MyServer] CREATING
++      ami: <none> => ami-0c4e4b4eb2e11d1d4
++      disable_api_termination: <none> => False
++      ebs_optimized: <none> => False
++      instance_id: <none> => <TBD>
++      name: <none> => my-demo-server
++      private_ip: <none> => <TBD>
++      public_ip: <none> => <TBD>
++      region: <none> => us-east-1
++      security_groups: <none> => [..instance.AllowSSH]
++      ssh_key: <none> => ..instance.MyKey
++      ssh_username: <none> => ec2-user
++      tags: <none> => None
++      type: <none> => t2.micro
++      user_data: <none> => None

Apply Changes? [y/N]: y

```

In the example above, you'll see how everything is being created for the first time. Stackzilla will list out the **attributes** for reach **resource**, along with their current and desired state.

-----------------------------------------

**NOTE**

For compute resources, Stackzilla will not consider creation complete until the host can be connected to via SSH. It may appear that the CLI command has hung, when in fact, it's simply waiting for the server to boot. Patience, padawan.

-----------------------------------------

With the `apply` operation complete, let's try connecting to the remote host and executing a command to check the available disk space.


```bash
$ stackzilla --namespace demo compute ssh --path my_blueprint.MyServer "df -H"
2022-11-09 12:27:18,611 (DEBUG:stackzilla-resource) Connecting to 54.166.232.215
Filesystem      Size  Used Avail Use% Mounted on
devtmpfs        507M     0  507M   0% /dev
tmpfs           515M     0  515M   0% /dev/shm
tmpfs           515M  422k  515M   1% /run
tmpfs           515M     0  515M   0% /sys/fs/cgroup
/dev/xvda1      8.6G  1.6G  7.0G  19% /
tmpfs           103M     0  103M   0% /run/user/1000
```

The `compute ssh` command allows you to execute any CLI command on the remote host. There are other, more programatic, ways of interacting with remote hosts which we'll cover in more advanced sections of blueprint authoring.

-----------------------------------------

__--path__

The `--path` parameter is the relative Python path to the blueprint resource for the CLI command to work on.
In this example, our entire blueprint was defined in `my_blueprint.py`. The EC2 server resource (a Python class) was named
`MyServer`. Thus, the relative Python path to our server would be `my_blueprint.MyServer`.

-----------------------------------------

## Cleaning up
It's irresponsible of us to just leave idle servers going, running up the AWS bill. Let's use Stackzilla to clean them up, ensuring that we won't get charged for idle resources. There are more important things in life to spend money on....like sponsoring open source projects. 😉

```bash
$stackzilla --namespace demo blueprint delete
Delete blueprint? [y/N]:
Resources in this deletion phase ['my_blueprint.MyServer']
Resources in this deletion phase ['my_blueprint.AllowSSH', 'my_blueprint.MyKey']
$
```

At this point, your namespace is empty. You can safely delete the file directly, or remove it with the `stackzilla delete <namespace>` command.
# Next Steps
Congrats on creating and workign with your first Stackzilla blueprint. We hope you can see how powerful Stackzilla is as an **Application ORM** development tool.

With that under your belt, it's time to move on to more advanced topics like:
- custom event handling
- host services
- using metadata in your blueprint
- custom CLI commands
- dependency graph injection
- writing a provider

If you have any questions, please join our [Discord server](https://discord.gg/CgNUkY3Xyj) or join the [GitHub discussions](https://github.com/Stackzilla/stackzilla/discussions).

Good luck! 🍀
