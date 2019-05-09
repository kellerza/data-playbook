"""DataEnvironment class."""
import pytest

from dataplaybook.const import PlaybookError
import dataplaybook.utils as utils

# pylint: disable=unsupported-assignment-operation,no-member,protected-access


def test_dataenvironment():
    """Test dataenvironment."""

    env = utils.DataEnvironment()
    env['tab'] = [1]
    assert env['tab'] == [1]

    with pytest.raises(Exception):
        env.tab2 = [1]
    assert 'tab2' not in env

    env.var.zz = 1
    assert env.var.zz == 1
    assert isinstance(env['var'], list)
    assert isinstance(env.var, dict)

    with pytest.raises(PlaybookError):
        env.var['non slug'] = 1

    with pytest.raises(Exception):
        env['var'] = 'notallowed'

    with pytest.raises(Exception):
        env.var = 'notallowed'

    assert list(env.keys()) == ['var', 'tab']


def test_env():
    """Test DataEnv."""
    dataenv = utils.DataEnvironment()
    assert isinstance(dataenv.var, dict)
    assert dataenv.var == {}
    assert isinstance(dataenv.var.env, dict)
    assert dataenv.var == {'env': {}}
    assert 'HOME' not in dataenv.var.env
    assert isinstance(dataenv.var.env.HOME, str)
    assert 'HOME' in dataenv.var.env

    with pytest.raises(PlaybookError):
        dataenv.var['env'] = 1


def test_dataenv():
    """Test DataEnv loading."""
    env = utils.DataEnv()
    env._load('a=1\nb="2"')
    assert env.a == '1'
    assert env.b == '"2"'

    env._load('a: 3\nb: "4"')
    assert env.a == '3'
    assert env.b == '"4"'


def test_logger():
    """Test logger."""
    utils.setup_logger()
    utils.set_logger_level({'dataplaybook': 'debug'})
