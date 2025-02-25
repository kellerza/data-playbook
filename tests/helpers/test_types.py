"""Test types."""

import attrs
import pytest

from dataplaybook.helpers.types import check_types


@attrs.define
class Ca:
    param: int = 1


def list_call(*, lst: list[str]) -> int:
    return 1


def list_call2(*, lst: list[Ca]) -> int:
    return 2


def test_args() -> None:
    check_types(list_call, kwargs={"lst": ["a", "b"]})

    with pytest.raises(TypeError):
        check_types(list_call, kwargs={"lst": ["a", 1]})

    with pytest.raises(TypeError):
        check_types(list_call2, kwargs={"lst": ["a", 1]})

    check_types(list_call2, kwargs={"lst": [Ca(1), Ca(2)]})

    with pytest.raises(TypeError):
        check_types(list_call2, kwargs={"lst": [Ca(1), 2]})

    check_types(list_call2, kwargs={"lst": [Ca(1), 2]}, retval=123)
