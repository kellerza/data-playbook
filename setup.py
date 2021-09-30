#!/usr/bin/env python
"""dataplaybook setup."""
from pathlib import Path
import re

from setuptools import setup


def find_version():
    """Retrieve the version."""
    constpy = Path("dataplaybook/const.py").read_text()
    version_match = re.search(r"^VERSION = ['\"]([^'\"]+)['\"]", constpy, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


VERSION = find_version()

desc = Path("README.md").read_text()

req = [r.strip() for r in Path("requirements.txt").read_text().splitlines()]
req = [r for r in req if r and not r.startswith("#")]

setup(
    name="dataplaybook",
    version=VERSION,
    long_description=desc,
    long_description_content_type="text/markdown",
    author="Johann Kellerman",
    author_email="kellerza@gmail.com",
    install_requires=req,
    test_suite="tests",
    entry_points={"console_scripts": ["dataplaybook = dataplaybook.__main__:main"]},
)
