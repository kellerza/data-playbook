#!/usr/bin/env python
"""dataplaybook setup."""
import re
from pathlib import Path

from setuptools import setup


def find_version():
    """Retrieve the version."""
    constpy = Path("dataplaybook/const.py").read_text()
    version_match = re.search(r"^VERSION = ['\"]([^'\"]+)['\"]", constpy, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


VERSION = find_version()

REQUIRES = [
    'colorlog',
    'attrs>=17.4.0',
    'voluptuous>=0.11.5',
    'pyyaml>=3.13,<4',
    'jinja2>=2.9,<3',
    'jmespath>=0.9.4,<1',
    'openpyxl>=2.6,<3',
]

setup(
    name='dataplaybook',
    version=VERSION,
    install_requires=REQUIRES,
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'dataplaybook = dataplaybook.__main__:main'
        ]},
)
