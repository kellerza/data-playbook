"""DataEnvironment class."""

import logging
import os
from pathlib import Path

from dataplaybook.utils import local_import_module, time_it
from dataplaybook.utils.logger import log_filter, set_logger_level, setup_logger

from ..conftest import import_folder

_LOGGER = logging.getLogger(__name__)


def test_logger() -> None:
    """Test logger."""
    setup_logger()
    set_logger_level({"dataplaybook": "debug"})


def test_filter() -> None:
    """Test log filter."""
    rec = logging.makeLogRecord({"args": [1, "aa", [1, 2], {"a": 1}]})
    assert log_filter(rec) is True

    rec.args[1] = "aa" * 1000  # type:ignore[index]
    assert len(str(rec.args[1])) > 200  # type:ignore[index]
    res = log_filter(rec)
    assert res.args[1].startswith("aa")
    assert "..." in res.args[1]
    assert len(res.args[1]) < 200


def test_local_import() -> None:
    """Test local import."""
    os.chdir("src/tests")
    try:
        tcom = local_import_module("common")
        assert tcom.COMMON is True
    finally:
        os.chdir("../..")


def test_timeit() -> None:
    """Test timeit context manager."""
    with time_it():
        print("a")


def test_local_import_all() -> None:
    """Test local import."""
    _LOGGER.info("Current folder %s", Path.cwd())

    with import_folder("./src/dataplaybook/tasks", "dataplaybook.tasks"):
        pass
