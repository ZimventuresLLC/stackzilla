---
permalink: /cli-guide/
layout: home
title: CLI Guide
---

# CLI Guide<i class="fas fa-terminal m-2"></i>
--------------------------------------------------------------------------------------------------------------

Welcome to the Stackzilla CLI guide. Here, you will find details about the functionality provided by running `stackzilla`. Each section (shown in the menu on the right) details a sub-command. Sub-commands encompass major areas of functionality such as: blueprints, compute, and metadata.

### Conventions

- Required CLI arguments that are enclosed with greater-than/less-than symbols.
  - Example: `--namespace <ns>`
- Optional CLI arguments are enclosed in brackets.
  - Example: `[--verify/--no-verify]`
- Flags will always have a positive and negative value. If the flag is optional, the default value is presented first.
  - Example: `[--verify/--no-verify]` -> `--verify` is the default in this case

### The `--namespace` parameter

Almost every `stackzilla` command requires a namespace in order to operate. This argument is the name of the database (excluding the `.db` file extension) that Stackzilla should use when running.

##### Example
Let's create a new namespace and then set a metadata key within it.

```bash
$ stackzilla --namespace zimventures init
$ ls -al zimventures*
-rw-r--r-- 1 vscode vscode 40960 Nov 11 00:19 zimventures.db
$ stackzilla --namespace zimventures metadata set --key foo --value "bar"
2022-11-11 00:20:45,253 (DEBUG:stackzilla-StackzillaSQLiteDB) Setting metadata on key = 'foo'
$
```

## Live Help<i class="fas fa-question m-2"></i>
--------------------------------------------------------------------------------------------------------------

Live help is available by executing any command with the `--help` flag.

##### Example
View help for the top-most level of Stackzilla.

```bash
 stackzilla --help
Usage: stackzilla [OPTIONS] COMMAND [ARGS]...

  Main entrypoint to all cli commands.

Options:
  --namespace TEXT  Text name for the new work environment  [required]
  --help            Show this message and exit.

Commands:
  blueprint   Command group for all blueprint CLI commands.
  compute     Command group for all compute CLI commands.
  database    Command group for all database CLI commands.
  delete      Delete an existing namespace.
  init        Initialize a new namespace.
  kubernetes  Command group for all compute CLI commands.
  metadata    Command group for all metadata CLI commands.
  resource    Command group for all resource CLI commands.
```

##### Example
View help for a specific command.
```bash
$ stackzilla --namespace foo metadata --help
Usage: stackzilla metadata [OPTIONS] COMMAND [ARGS]...

  Command group for all metadata CLI commands.

Options:
  --help  Show this message and exit.

Commands:
  delete  Delete the specified metadata entry.
  exists  Test if a metadata key exists.
  get     Query the value for the specified metadata entry.
  set     Set the metadata value for the specified key.
```

# Blueprint<i class="far fa-tools m-2"></i>
--------------------------------------------------------------------------------------------------------------

The `blueprint` command exposes all of the functionality needed to work with your blueprint.

## apply<i class="fas fa-layer-plus m-2"></i>
--------------------------------------------------------------------------------------------------------------

`stackzilla --namespace <ns> blueprint apply --path <path>

Blueprint appplication (`apply`) is one of the most important commands you'll use. with Stackzilla. The `apply` command is actually a multi-phase command. It performs the following operations:

- Blueprint Verification
- Blueprint Diffing
- User Confirmation
- Blueprint Application

The verification phase ensures the blueprint is syntactically valid, required attributes are defined, and attribute values are valid. The difffing phase compares a blueprint's on-disk version against what is in the database. If the user confirms what is shown, the apply phase will be executed.

### Blueprint Diff
The diff that is shown will let the user know which resources are being creaed, deleted, and modified. In addition, individual attribute values are shown with pre and post application values. Secret attributes are simply displayed with the value `<secret>`.  See the sections below for example output of each diff result.

#### Example New Resource
```bash
[key.MyKey] CREATING
++      arn: <none> => <TBD>
++      format: <none> => pem
++      key_fingerprint: <none> => <TBD>
++      key_material: <none> => <secret>
++      key_pair_id: <none> => <TBD>
++      name: <none> => zim-key
++      region: <none> => us-east-1
++      tags: <none> => {'project': 'stackzilla-provider-aws'}
++      type: <none> => rsa
```

#### Example Deleted Resource
```bash
[key.MyKey] DELETING
--      arn
--      format
--      key_fingerprint
--      key_material
--      key_pair_id
--      name
--      region
--      tags
--      type
```

#### Example Modified (With Rebuild)
If an attribute is modified that has flagged the resource for rebuild, special output will be displayed.

```bash
[key.MyKey] REBUILD REQUIRED. See attributes marked with "!!"
!!      region: us-east-1 => us-east-2
```

#### Example Modified
```bash
[key.MyKey] UPDATING
@@      tags: {'project': 'stackzilla-provider-aws'} => {'project': 'stackzilla-provider-aws-new'}
```

### Blueprint Application
*This is where the magic happens! 🪄*

The application phase works on the results from the diff phase. Resources that have changes, been added, or been deleted, are organized into a [dependency graph](https://en.wikipedia.org/wiki/Dependency_graph). The dependency graph is resolved into a list of *phases*. Each phase ensures the following conditions are met:

- Resources within a phase do not depend on each other
- Any dependencies or the current resource have aleady been applied

#### Application Failure
At the conclusion of a phase, if any of the resources failed application, the remainder of the application will be aborted. Resources that were successfully applied will *NOT* be terminated. At this point the user can resolve whatever the issue was and re-run `apply`. The re-apply will pick up where the last one left off.

## delete<i class="fas fa-layer-minus m-2"></i>

--------------------------------------------------------------------------------------------------------------

`stackzilla --namespace <ns> blueprint delete [--dry-run/--no-dry-run]`

The `delete` command will (shockingly) delete your blueprint. "Deleting your blueprint" means that any resources which have been provisioned (applied) will be deleted. Once the provider has successfully deleted the resource, Stackzilla removes it from the namesapce database.

## diff<i class="fal fa-not-equal m-2"></i>
--------------------------------------------------------------------------------------------------------------

`stackzilla --namespace <ns> blueprint diff --path <path> [--verify|--no-verify]`

The `diff` command will show the *difference* between the on-disk version of your blueprint and what is stored in the namesapce database. Prior to Stackzilla applying a blueprint, it will always perform a diff, and display that to the user. Running the `diff` command will perform that functionality, outside of the context of a blueprint application.

{% capture verify_note %}
By default, a blueprint verification will be executed prior to running the diff. If something is wrong with your blueprint (syntax, missing required attributes, etc...) then the command will fail with a verification error. A blueprint diff will not be displayed if a verification error occurs. See the <a href="#verify">verify command</a> for details on error messages and exit codes for verification.
{% endcapture %}
{% include note-info.html content=verify_note %}


##### Example
```bash
$ stackzilla --namespace foo blueprint diff --path ./example_blueprints/just_a_key/ --no-verify
[instance.MyKey] CREATING
++      key_size: <none> => 2048
++      private_key: <none> => <secret>
++      public_key: <none> => <TBD>
```
## verify<a href="#verify"><i class="fal fa-check-circle m-2"></i></a>
--------------------------------------------------------------------------------------------------------------

`stackzilla --namespace <ns> blueprint verify --path <path>`

Blueprint verificaiton always occurs as the first step during `stackzilla apply`. In some cases, it is useful to verify the blueprint, outside of the context of it being applied. For example, say you want to verify your blueprint when pushing to a branch in source control. The CI job could simply run `stackzilla verify` against the modified blueprint and the result could be a status for the commit.

A `--namespace` **is** required for the command to run. It's possible that the blueprint may pull attribute values from metadata.

##### Success
When the verify command completes successfully, `Verified` is printed to STDOUT, and an exit code of 0 is returned by `stackzilla`.

```bash
$ stackzilla --namespace foo blueprint verify --path ./example_blueprints/single_volume/
Verified
$ echo $?
0
```

##### Failure
For the failure scenario, a contextual error message is displayed and an exit code of `1` is returned by `stackzilla`.

```bash
$ stackzilla --namespace foo blueprint verify --path ./example_blueprints/single_volume/
[instance.MyServer]
!!region
        None is not one of the available choices: ['ap-northeast', 'ap-southap-southeast', 'ap-west', 'ca-central', 'us-central', 'us-east', 'us-southeast', 'us-west', 'eu-central', 'eu-west']
        Attribute is required but value is None

Error: Blueprint verification failed
$ echo $?
1
```
# Compute <i class="fas fa-server m-2"></i>
--------------------------------------------------------------------------------------------------------------
If you've provisioned compute resources from a blueprint, then you'll certainly be interested in running `compute` commands.

## ssh<i class="fal fa-terminal m-2"></i>
--------------------------------------------------------------------------------------------------------------

`stackzilla --namespace <ns> compute ssh --path <path> command`

The `compute ssh` command provides a way for you to execute a single commmand on a compute instance.

## start<i class="far fa-play m-2"></i>
--------------------------------------------------------------------------------------------------------------

`stackzilla --namespace <ns> compute start --path <path> [--wait/--no-wait]`

For instanes that have been shut down, the `compute start` command will power them back on. By default, the command will not reutrn until the instance is reachable via SSH. If an asyncronous invocation is required, pass in the `--no-wait` flag.


## stop<i class="fal fa-stop m-2"></i>
--------------------------------------------------------------------------------------------------------------

`stackzilla --namespace <ns> compute stop --path <path> [--wait/--no-wait]`

One way to save money on your compute costs is to *turn them off*! The `compute stop` command will shut down an instance.
By default, the command will not return until the shutdown is complete. If an async operation is required, use the `--no-wait` flag.

# Kubernetes<i class="fas fa-dharmachakra m-2"></i>
--------------------------------------------------------------------------------------------------------------
For Kubernetes clusters, a generic set of implementation agnostic commands are offered by Stackzilla.

## get-kubeconfig<i class="far fa-file m-2"></i>
--------------------------------------------------------------------------------------------------------------

`stackzilla --namespace <ns> kubernetes get-kubeconfig --path <path>`
The `kubernetes get-kubeconfig` command will fetch the kubeconf file and render it to STDOUT.


## show<i class="fad fa-search m-2"></i>
--------------------------------------------------------------------------------------------------------------

`stackzilla --namespace <ns> kubernetes show --path <path>`

The `kubernetes show` command will display details about a provisioned Kubernetes cluster.

# Metadata<i class="fas fa-table m-2"></i>
--------------------------------------------------------------------------------------------------------------
The `metadata` suite of commands allow you to interact with the namespace key/value store.

## delete<i class="fas fa-file-minus m-2"></i>
--------------------------------------------------------------------------------------------------------------
`stackzilla --namespacer <ns> metadata delete --key <key>`

Remove a key from the metadata store. If the key is not found, an error is displayed to STDOUT and the command exits with code `1`.

## exists<i class="fas fa-file-search m-2"></i>
--------------------------------------------------------------------------------------------------------------
`stackzilla --namespacer <ns> metadata exists --key <key>`
 Queries if a key exists in the metadata store. `true` or `false` is displayed to STDOUT, depending on the presence of the key. The exit code for this command is always `0`, unless a namespace or other internal error occurs.

```bash
$ stackzilla --namespace test metadata exists --key foo
true
$ stackzilla --namespace test metadata exists --key nope
false
```

## get<i class="fas fa-file m-2"></i>
--------------------------------------------------------------------------------------------------------------
`stackzilla --namespacer <ns> metadata get --key <key>`
Get the value for a key in the metadata store. The key value is printed. to STDOUT if it is found. If the key is not found, an error message is displayed and an exit code of `1` is returned.

```bash
$ stackzilla --namespace test metadata get --key foo
Error: key (foo) not found
$ echo $?
1

$ stackzilla --namespace test metadata set --key foo --value "bar"

$ stackzilla --namespace test metadata get --key foo
bar
$ echo $?
0
```
## set<i class="fas fa-file-plus m-2"></i>
--------------------------------------------------------------------------------------------------------------
`stackzilla --namespacer <ns> metadata set --key <key> --value <value>`
The `metadata set` command will create or overwrite a key in the namespace metadata.

# resource<i class="fas fa-box-open m-2"></i>
--------------------------------------------------------------------------------------------------------------

The `resource` command provides an interface for viewing and modifying resources within a namespace.

## show<i class="fad fa-search m-2"></i>
--------------------------------------------------------------------------------------------------------------
`stackzilla --namespace <ns> resource show --path <path>`


The `resource show` command will display details about a provisioned resource. Details about the resource are pulled from the namespace metadata.

```bash
$ stackzilla --namespace test resource show --path key.MyKey
[key.MyKey]
arn: arn:aws:ec2:us-east-1:123456789ABC:key-pair/key-1234567890abcdefg
format: pem
key_fingerprint: 2b:07:68:15:4c:c1:31:cd:69:08:7d:9b:40:f5:53:f3:e9:c4:9d:dd
key_material: <secret>
key_pair_id: key-1234567890abcdefg
name: zim-key
region: us-east-1
tags: {'project': 'stackzilla-provider-aws'}
type: rsa
```
