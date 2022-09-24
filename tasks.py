"""Tasks that can be executed via 'invoke <cmd>' for developers."""
from invoke import task

source_root = 'stackbot'

@task
def lint(c):
    """Perform linting duties on the codebase."""
    c.run(f'isort {source_root}')
    c.run(f'pydocstyle {source_root}')
    c.run(f'pyflakes ./${source_root}')
    c.run(f'pylint ./${source_root}')

@task
def test(c):
    """Run all of the tests!"""
    c.run(f'pytest {source_root}')
