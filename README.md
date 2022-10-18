# Stackzilla

[![codecov](https://codecov.io/gh/Stackzilla/stackzilla/branch/main/graph/badge.svg?token=SJQBB59GJ7)](https://codecov.io/gh/Stackzilla/stackzilla)

Stackzilla is a Python ORM for managing application infrastructure and software. Stackzilla's object-oriented design allows for complete customization by the developer, if that level of customization is needed. For simpler deployments, Stackzilla offers an incredibly easy interface for Python developers to work with.

# Installation
Install and update using [pip](https://pip.pypa.io/en/stable/getting-started/).

```bash
pip install -U stackzilla
```

View the Stackzilla PyPI package [here](https://pypi.org/project/stackzilla/).

# Usage
## A simple blueprint
TBD: Pending the first provider being published!

## Provisioning
```bash
stackzilla --namespace hello_blueprint init
stackzilla --namespace hello_blueprint blueprint apply --path ./myblueprint/
... (show output)
stackzilla --namespace hello_blueprint blueprint delete
```

# Have a question?
All support requests are handled through [GitHub Discussions](https://github.com/Stackzilla/stackzilla/discussions). Please only open a [GitHub issue](https://github.com/Stackzilla/stackzilla/issues) if you've found a bug, or have a feature request.

# Contributing
To get started with contributing to the Stackzilla project, visit the developer documentation. Thank you for your interest!

# License
Stackzilla is licensed under the GNU Affero General Public License v3.0 license See [LICENSE](https://github.com/Stackzilla/stackzilla/blob/main/LICENSE) for more information.
