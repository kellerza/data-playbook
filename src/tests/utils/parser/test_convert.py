"""Test converter."""

from datetime import datetime

import attrs
import cattrs
import pytest
from whenever import Instant

from dataplaybook.utils.parser import CONVERT, BaseClass, _structure1


@attrs.define
class TstModel(BaseClass):
    """Test class."""

    text: str = ""
    list_is: list[int | str] = attrs.field(factory=list)
    list_i: list[int] = attrs.field(factory=list)
    list_s: list[str] = attrs.field(factory=list)
    set_i: set[int] = attrs.field(factory=set)


def test_convert1() -> None:
    """Test."""
    res = _structure1(
        CONVERT,
        {"junk": "aa", "list_is": [0, "1", "z"]},
        TstModel,
        allow_ignore_extra=True,
    )

    assert res == TstModel(list_is=[0, 1, "z"])


def test_set() -> None:
    """Test sets."""
    res = TstModel.structure(
        {
            "list_i": [1, 2, 3],
            "set_i": {3, 4, 5},
            "list_s": ["a", "b"],
        }
    )
    assert res.list_i == [1, 2, 3]
    assert res.list_s == ["a", "b"]
    assert res.set_i == {3, 4, 5}


def test_int() -> None:
    """Int."""
    for val, exp in [("1", 1), (2, 2), (True, 1), (False, 0)]:
        assert CONVERT.structure(val, int) == exp

    for val in [
        ["1", 2],
        ["1", "2"],
        "1,2",
        "[1,2]",
        '["1",2]',
        '["1","2"]',
    ]:
        assert CONVERT.structure(val, list[int]) == [1, 2]
        assert CONVERT.structure(val, set[int]) == {1, 2}

    for val in ["1.0", "a"]:
        with pytest.raises(ValueError):
            CONVERT.structure(val, int)

    with pytest.raises(TypeError):
        CONVERT.structure([1, 2], int)

    for val in [
        [1, "a"],
        [1, "2.0"],
    ]:
        with pytest.raises(ValueError):
            CONVERT.structure(val, list[int])


def test_float_int() -> None:
    """Int."""
    for val, exp in [("1", 1), ("2.2", 2.2), (True, 1), ("5.00", 5), (5.0, 5)]:
        assert CONVERT.structure(val, int | float) == exp  # type: ignore[arg-type]
        assert CONVERT.structure(val, int | float | None) == exp  # type: ignore[arg-type]


def test_int_str() -> None:
    """Test int|str."""
    for val, exp in [
        ("1", 1),
        (1, 1),
        ("a", "a"),
    ]:
        assert CONVERT.structure(val, int | str) == exp  # type: ignore[arg-type]


def test_optional() -> None:
    """Test optional."""
    val = None
    assert CONVERT.structure(val, int | None) is None  # type: ignore[arg-type]
    assert CONVERT.structure(val, list[int] | None) is None  # type: ignore[arg-type]
    assert CONVERT.structure(val, set[int] | None) is None  # type: ignore[arg-type]

    with pytest.raises(cattrs.errors.StructureHandlerNotFoundError):
        assert CONVERT.structure(val, int | str | None) is None  # type: ignore[arg-type]


def test_date_Instant() -> None:
    """Date."""
    inst = CONVERT.structure("2022-06-26", Instant)
    assert inst == Instant.from_utc(2022, 6, 26)

    # inst = Instant.now()
    idate = CONVERT.unstructure(inst, Instant)
    assert isinstance(idate, datetime)
    assert idate == inst.py_datetime()
