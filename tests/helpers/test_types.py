"""Test types."""

from collections import abc
from typing import Any

import pytest
from typeguard import TypeCheckError, typechecked

from dataplaybook.helpers.types import typeguard

RowDataGen = abc.Generator[dict[str, Any], None, None]


@typechecked
def return_some_bad(lst: list[str]) -> RowDataGen:
    """Return None."""
    for val in lst:
        yield ({"a": val})


@typechecked
def return_some_good(lst: list[str]) -> abc.Generator[dict[str, Any], None, None]:
    """Return None."""
    for val in lst:
        yield ({"a": val})


def test_return_some():
    """Test return_none."""
    assert list(return_some_good(["1", "2"])) == [{"a": "1"}, {"a": "2"}]
    assert list(return_some_good([])) == []

    with pytest.raises(TypeCheckError) as err:
        assert list(return_some_bad(["1", "2"])) == [{"a": "1"}, {"a": "2"}]
    assert "is not an instance of collections.abc.Generator" in str(err)

    with pytest.raises(TypeCheckError):
        assert list(return_some_bad([])) == []
    assert "is not an instance of collections.abc.Generator" in str(err)


def test_some_check_all() -> None:
    """Ensure config was ok."""
    assert (
        typeguard.config.collection_check_strategy
        == typeguard.CollectionCheckStrategy.ALL_ITEMS
    )
    with pytest.raises(TypeCheckError) as err:
        list(return_some_good(["1", 2]))  # type:ignore
    assert "is not an instance of str" in str(err)
