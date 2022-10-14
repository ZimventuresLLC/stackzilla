"""Setuptools configuration file."""
import os

from setuptools import setup, find_namespace_packages

# Meta information
version = open('VERSION').read().strip()
dirname = os.path.dirname(__file__)

# Save version and author to __meta__.py
path = os.path.join(dirname, 'stackzilla', '__meta__.py')
data = (
    f'"""Package versioning info."""'
    f"# Automatically created. Please do not edit.\n"
    f"# noqa\n"
    f"__version__ = '{version}'\n"
    f"__author__ = 'Zimventures, LLC'\n"
)

with open(path, 'wb') as F:
    F.write(data.encode())

# Read in all of the requirements to install/run Stackzilla
install_requirements = []
with open('requirements.txt') as requirements:
    for package in requirements.readlines():
        install_requirements.append(package)

# Read in all of the requirements to run the tests on the Stackzilla codebase
testing_requirements = []
with open('requirements-testing.txt') as testing_req_fh:
    for package in testing_req_fh.readlines():
        testing_requirements.append(package)

setup(
    # Basic info
    name='stackzilla',
    version=version,
    author='Zimventures, LLC',
    author_email='stackzilla@zimventures.com',
    url='https://github.com/zimventures/stackzilla',
    description='Provision your stack - with a snake!',
    long_description=open('README.md').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],

    # Packages and depencies
    package_dir={'stackzilla': 'stackzilla'},
    packages=find_namespace_packages(include=['stackzilla.blueprint',
                                            'stackzilla.cli',
                                            'stackzilla.provider',
                                            'stackzilla.database',
                                            'stackzilla.resource'
                                            'stackzilla.utils']),
    include_package_data=True,
    namespace_packages=['stackzilla'],
    install_requires=install_requirements,
    extras_require={
        'testing': testing_requirements,
    },

    # Data files
    package_data={},

    # Scripts
    entry_points={
        'console_scripts': [
            'stackzilla=stackzilla.cli.main:cli'],
    },

    # Other configurationss
    zip_safe=False,
    platforms='any',
)
