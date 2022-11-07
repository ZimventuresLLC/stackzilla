---
permalink: /getting-started/
layout: home
title: Getting Started
---

# Welcome

Welcome to Stackzilla!

# Install Stackzilla

Stackzilla is distributed via [PyPI](https://pypi.org/project/stackzilla/). Installing it is as easy as running `pip stackzilla`.

## Provider Installation
"Out of the box", Stackzilla does not have the abililty to provision or configure anything. Instead, it relies on **provider** plugins. These providers can also be installed via `pip`. All provider modules will be prefixed with `stackzilla-provider-`.

_Example: `stackzilla-provider-linode`_

# Your First Blueprint

Let's get started by creating our first blueprint. The blueprint is a definition of what we want Stackzilla to create. In this case, we'd like it to create a server on [Linode](linode.com), secured with an SSH key. You will need an `access token` which can be obtained by following [this guide](https://www.linode.com/docs/guides/getting-started-with-the-linode-api/#create-an-api-token). With the new token in hand, insert it in the blueprint at the area marked `<your_token_here>`.

-------------------------
##### _**HEADS UP!**_

API Tokens should be considered as private as a password. Do NOT check your blueprint into source control, or share it with anyone. In a production environment, you would likely retrieve your token from a secrets manager or environment variable.

-------------------------

Create a new directory, `my_blueprint`, and inside of it, drop an empty `__init__.py`. Within the newly created directory, open `instance.py` and add the contents of the file below.

<script src="https://gist.github.com/zimventures/f1a532b4bff1322c547198e564bde8ec.js"></script>

We won't go deep into the details of the blueprint and how you can customize them to fit your needs. What is worth pointing out is that this blueprint contains two _resources_: An SSH Key and an Insatance. Within each of these resources, _attributes_ define properties of the resource.

At this point, your blueprint is ready for verification and application. Buckle up - it's about to get fun!
## Applying The Blueprint

# Blueprint Updates
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
# Cleaning Up
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
# Next Steps
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
