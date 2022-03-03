"""DataEnvironment class."""
import logging
import os
from pathlib import Path

import pytest

import dataplaybook.utils as utils
from dataplaybook.main import ALL_TASKS

# pylint: disable=unsupported-assignment-operation,no-member,protected-access

_LOGGER = logging.getLogger(__name__)


def test_dataenvironment():
    """Test dataenvironment."""

    env = utils.DataEnvironment()
    env["tab"] = [1]
    assert env["tab"] == [1]

    with pytest.raises(Exception):
        env.tab2 = [1]
    assert "tab2" not in env

    env.var.zz = 1
    assert env.var.zz == 1
    assert isinstance(env["var"], list)
    assert isinstance(env.var, dict)

    with pytest.raises(KeyError):
        env.var["non slug"] = 1

    with pytest.raises(Exception):
        env["var"] = "notallowed"

    with pytest.raises(Exception):
        env.var = "notallowed"

    assert list(env.keys()) == ["var", "tab"]

    env["v"] = 1
    assert env.var.v == 1


def test_dataenvironment_as():
    """Test dataenvironment."""

    env = utils.DataEnvironment()
    env["t1"] = [{"a": 1}]

    assert len(env.as_dict("b", "c")) == 0
    assert len(env.as_list("b", "c")) == 0

    assert len(env.as_dict("t1", "c")) == 1
    assert len(env.as_list("t1", "c")) == 1

    assert env.as_list("t1") == [[{"a": 1}]]
    assert env.as_dict("t1")["t1"] == [{"a": 1}]


def test_env():
    """Test DataEnv."""
    dataenv = utils.DataEnvironment()
    assert isinstance(dataenv.var, dict)
    assert dataenv.var == {}
    assert isinstance(dataenv.var.env, dict)
    assert dataenv.var == {"env": {}}

    # if not os.getenv("HOME"):
    os.environ["HOME"] = "/home/me"

    assert "HOME" not in dataenv.var.env
    assert isinstance(dataenv.var.env.HOME, str)
    assert "HOME" in dataenv.var.env
    assert dataenv.var.env.HOME == "/home/me"

    with pytest.raises(KeyError):
        dataenv.var["env"] = 1


def test_dataenv():
    """Test DataEnv loading."""
    env = utils.DataEnv()
    env._load('a=1\nb="2"')
    assert env.a == "1"
    assert env.b == '"2"'

    env._load('a: 3\nb: "4"')
    assert env.a == "3"
    assert env.b == '"4"'


def test_logger():
    """Test logger."""
    utils.setup_logger()
    utils.set_logger_level({"dataplaybook": "debug"})


def test_filter():
    """Test log filter."""

    rec = logging.makeLogRecord({"args": [1, "aa", [1, 2], {"a": 1}]})
    assert utils.log_filter(rec) is True

    rec.args[1] = "aa" * 1000
    assert len(rec.args[1]) > 200
    res = utils.log_filter(rec)
    assert res.args[1].startswith("aa")
    assert "..." in res.args[1]
    assert len(res.args[1]) < 200


def test_local_import():
    """Test local import."""
    os.chdir("tests")
    try:
        tcom = utils.local_import_module("common")
        assert tcom.COMMON is True
    finally:
        os.chdir("..")


def test_timeit():
    """Test timeit context manager."""
    with utils.time_it():
        print("a")


def _glob_import(path):
    cwd = os.getcwd()
    try:
        for file in path.glob("**/*.py"):
            os.chdir(file.parent)
            _LOGGER.info(str(file))
            utils.local_import_module(file.stem)
    finally:
        ALL_TASKS.clear()
        os.chdir(cwd)


def test_local_import_all():
    """Test local import."""
    _glob_import(Path("./dataplaybook").resolve(strict=True))
