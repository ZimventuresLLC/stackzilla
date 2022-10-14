"""Tasks that can be executed via 'invoke <cmd>' for developers."""
from invoke import task

source_root = 'stackzilla'

@task
def lint(c):
    """Perform linting duties on the codebase."""
    c.run(f'isort {source_root}')
    c.run(f'pydocstyle {source_root}')
    c.run(f'pylint ./{source_root}')

@task
def test(c):
    """Run all of the tests!"""
    c.run(f'pytest {source_root}')

@task
def serve_docs(c):
    """Start a server to view and automatically buidl documnetation."""
    c.run('sphinx-autobuild docs docs/_build/html/')

@task
def build(c):
    """Build a wheel"""
    c.run('python -m pip install build twine')
    c.run('python setup.py bdist_wheel --universal')

def publish_test(c):
    """Publish the distribution to the test PyPI server"""
    c.run('twine upload -r testpypi dist/* ')

def publish(c):
    """Publish the distribution to the production PyPI server"""
    c.run('twine upload dist/*')
