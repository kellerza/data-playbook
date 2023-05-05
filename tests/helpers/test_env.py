"""Test Environment"""
import os

import pytest

from dataplaybook.helpers.env import DataEnvironment, _DataEnv


def test_dataenvironment():
    """Test dataenvironment."""

    env = DataEnvironment()
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

    env = DataEnvironment()
    env["t1"] = [{"a": 1}]

    assert len(env.as_dict("b", "c")) == 0
    assert len(env.as_list("b", "c")) == 0

    assert len(env.as_dict("t1", "c")) == 1
    assert len(env.as_list("t1", "c")) == 1

    assert env.as_list("t1") == [[{"a": 1}]]
    assert env.as_dict("t1")["t1"] == [{"a": 1}]


def test_env():
    """Test DataEnv."""
    dataenv = DataEnvironment()
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
    env = _DataEnv()
    env._load('a=1\nb="2"')
    assert env.a == "1"
    assert env.b == '"2"'

    env._load('a: 3\nb: "4"')
    assert env.a == "3"
    assert env.b == '"4"'
