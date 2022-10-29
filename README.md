# Stackzilla

<p style="text-align:center">
    <img src="https://github.com/Stackzilla/stackzilla/blob/main/docs/assets/images/zilla_and_blocks.png?raw=true"  alt="stackzilla" width="500"/>
</p>

[![codecov](https://codecov.io/gh/Stackzilla/stackzilla/branch/main/graph/badge.svg?token=SJQBB59GJ7)](https://codecov.io/gh/Stackzilla/stackzilla)
[![unit-test](https://github.com/Stackzilla/stackzilla/actions/workflows/branch-push-unit-test.yml/badge.svg)](https://github.com/Stackzilla/stackzilla/actions/workflows/branch-push-unit-test.yml)
[![Python 3.7 | 3.8 | 3.9 | 3.10](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)](https://pypi.org/project/stackzilla/)
[![pyPI](https://img.shields.io/pypi/v/stackzilla)](https://pypi.org/project/stackzilla/)

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
