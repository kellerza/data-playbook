#!/usr/bin/env python
"""dataplaybook setup."""
import re

from setuptools import setup


def find_version():
    """Retrieve the version."""
    with open("dataplaybook/const.py") as const_py:
        version_match = re.search(r"^VERSION = ['\"]([^'\"]+)['\"]",
                                  const_py.read(), re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string.")


VERSION = find_version()
print('version', VERSION)

REQUIRES = [
    'attrs>=17.4.0',
    'voluptuous>=0.11.1',
    'pyyaml>=3.11,<4',
    'openpyxl>=2.5,<3',
]

MIN_PY_VERSION = '3.5.3'
REPO = 'https://github.com/kellerza/data-playbook'

setup(
    name='dataplaybook',
    version=VERSION,
    description="Playbooks for data. Open, process and save table based data.",
    url=REPO,
    download_url="{}/tarball/{}".format(REPO, VERSION),
    author='Johann Kellerman',
    author_email='kellerza@gmail.com',
    license="Apache License 2.0",
    install_requires=REQUIRES,
    python_requires='>={}'.format(MIN_PY_VERSION),
    test_suite='tests',
    packages=['dataplaybook'],
    entry_points={
        'console_scripts': [
            'dataplaybook = dataplaybook.__main__:main'
        ]},
    zip_safe=True
)
