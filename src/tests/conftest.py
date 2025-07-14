"""Test helpers."""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from importlib import import_module
from pathlib import Path

from dataplaybook.main import ALL_TASKS, Task
from dataplaybook.utils import local_import_module

_LOGGER = logging.getLogger(__name__)


@contextmanager
def import_folder(
    path_str: str, modname: str = "", glob: str = "*.py"
) -> Generator[dict[str, Task], None, None]:
    """Import all modules in a folder."""
    path = Path(path_str).resolve(strict=True)
    cwd = Path.cwd()
    try:
        for file in path.glob(glob):
            if modname:
                imp = modname if file.stem == "__init__" else f"{modname}.{file.stem}"
                import_module(imp)
                continue
            os.chdir(file.parent)
            _LOGGER.info(str(file))
            local_import_module(file.stem)
        os.chdir(cwd)
        yield ALL_TASKS
    finally:
        ALL_TASKS.clear()
        os.chdir(cwd)
