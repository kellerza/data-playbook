"""Config Validation Tests."""

import pytest

from dataplaybook.utils import AttrDict, AttrKeyError


def test_attrd():
    atd = AttrDict(a=1, b=2)
    assert atd.a == 1
    assert atd["a"] == 1
    assert atd.b == 2
    with pytest.raises(AttrKeyError):
        assert atd.z is None
    atd["z"] = 1
    with pytest.raises(IOError):
        atd.z = 2
    assert atd.z == 1
    assert "z=" in str(atd)
