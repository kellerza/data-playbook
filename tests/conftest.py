import logging
import os
from contextlib import contextmanager
from pathlib import Path

from dataplaybook.main import ALL_TASKS
from dataplaybook.utils import local_import_module

_LOGGER = logging.getLogger(__name__)


@contextmanager
def import_folder(path_str: str, glob: str = "*.py"):
    path = Path(path_str).resolve(strict=True)
    cwd = os.getcwd()
    try:
        for file in path.glob(glob):
            os.chdir(file.parent)
            _LOGGER.info(str(file))
            local_import_module(file.stem)
        os.chdir(cwd)
        yield ALL_TASKS
    finally:
        ALL_TASKS.clear()
        os.chdir(cwd)
