"""Tasks that can be executed via 'invoke <cmd>' for developers."""
from invoke import task

source_root = 'stackzilla'

@task
def clean(c):
    """Clean out any build files or Python caches."""
    c.run('py3clean .')

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
def build(c):
    """Build a wheel"""
    c.run('python -m pip install build twine')
    c.run('python setup.py bdist_wheel --universal')

@task
def publish_test(c):
    """Publish the distribution to the test PyPI server"""
    c.run('twine upload -r testpypi dist/* ')

@task
def publish(c):
    """Publish the distribution to the production PyPI server"""
    c.run('twine upload dist/*')

@task
def serve_docs(c):
    """Start running the Jekyll server to serve documentation."""
    c.run('cd ./docs; bundle exec jekyll serve')
