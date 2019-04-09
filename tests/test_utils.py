"""DataEnvironment class."""
from dataplaybook.const import PlaybookError
from dataplaybook.utils import DataEnvironment

import pytest


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
