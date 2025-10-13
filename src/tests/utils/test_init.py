"""DataEnvironment class."""

import logging
import os
from pathlib import Path

from dataplaybook.utils import local_import_module, time_it
from dataplaybook.utils.logger import log_trim_messages, set_LOG_level, setup_LOG

from ..conftest import import_folder

_LOG = logging.getLogger(__name__)


def test_LOG() -> None:
    """Test logger."""
    setup_LOG()
    set_LOG_level({"dataplaybook": "debug"})


def test_filter() -> None:
    """Test log filter."""
    rec = logging.makeLogRecord({"args": [1, "aa", [1, 2], {"a": 1}]})
    assert log_trim_messages(rec) is True

    rec.args[1] = "aa" * 1000  # type:ignore[index]
    assert len(str(rec.args[1])) > 200  # type:ignore[index]
    res = log_trim_messages(rec)
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
    _LOG.info("Current folder %s", Path.cwd())

    with import_folder("./src/dataplaybook/tasks", "dataplaybook.tasks"):
        pass
