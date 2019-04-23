"""DataEnvironment class."""
import pytest

from dataplaybook.const import PlaybookError
from dataplaybook.utils import DataEnvironment


def test_dataenvironment():
    """Test dataenvironment."""

    env = DataEnvironment()
    env['tab'] = [1]
    assert env['tab'] == [1]

    with pytest.raises(Exception):
        env.tab2 = [1]
    assert 'tab2' not in env

    env.var.zz = 1
    assert env.var.zz == 1  # pylint: disable=no-member

    with pytest.raises(PlaybookError):
        env.var['non slug'] = 1

    with pytest.raises(Exception):
        env['var'] = 'notallowed'

    with pytest.raises(Exception):
        env.var = 'notallowed'

    assert list(env.keys()) == ['var', 'tab']


def test_env():
    """Test DataEnv."""
    # pylint: disable=no-member
    dataenv = DataEnvironment()
    assert isinstance(dataenv.var, dict)
    assert dataenv.var == {}
    assert isinstance(dataenv.var.env, dict)
    assert dataenv.var == {'env': {}}
    assert 'HOME' not in dataenv.var.env
    assert isinstance(dataenv.var.env.HOME, str)
    assert 'HOME' in dataenv.var.env

    with pytest.raises(PlaybookError):
        dataenv.var['env'] = 1
