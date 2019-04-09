"""Common test helpers."""
import logging
import os
from pathlib import Path
# from unittest.mock import patch

from dataplaybook import loader

_LOGGER = logging.getLogger(__name__)


def load_module(filename):
    """Change older and load."""
    pth = Path(filename)
    os.chdir(pth.parent)
    loader.remove_module(pth.stem)
    loader.load_module(pth.stem)
