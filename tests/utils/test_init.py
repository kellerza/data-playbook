"""DataEnvironment class."""
import logging
import os
from pathlib import Path

from dataplaybook.main import ALL_TASKS
from dataplaybook.utils import local_import_module, time_it
from dataplaybook.utils.logger import log_filter, set_logger_level, setup_logger

# pylint: disable=unsupported-assignment-operation,no-member,protected-access

_LOGGER = logging.getLogger(__name__)


def test_logger():
    """Test logger."""
    setup_logger()
    set_logger_level({"dataplaybook": "debug"})


def test_filter():
    """Test log filter."""

    rec = logging.makeLogRecord({"args": [1, "aa", [1, 2], {"a": 1}]})
    assert log_filter(rec) is True

    rec.args[1] = "aa" * 1000
    assert len(rec.args[1]) > 200
    res = log_filter(rec)
    assert res.args[1].startswith("aa")
    assert "..." in res.args[1]
    assert len(res.args[1]) < 200


def test_local_import():
    """Test local import."""
    os.chdir("tests")
    try:
        tcom = local_import_module("common")
        assert tcom.COMMON is True
    finally:
        os.chdir("..")


def test_timeit():
    """Test timeit context manager."""
    with time_it():
        print("a")


def _glob_import(path):
    cwd = os.getcwd()
    try:
        for file in path.glob("**/*.py"):
            os.chdir(file.parent)
            _LOGGER.info(str(file))
            local_import_module(file.stem)
    finally:
        ALL_TASKS.clear()
        os.chdir(cwd)


def test_local_import_all():
    """Test local import."""
    _glob_import(Path("./dataplaybook").resolve(strict=True))
