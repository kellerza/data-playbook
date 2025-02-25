"""Ensure."""

from datetime import datetime, timezone

import pytest
from whenever import Instant

from dataplaybook.utils.ensure import (
    ensure_bool,
    ensure_bool_str,
    ensure_datetime,
    ensure_instant,
    ensure_list,
    ensure_string,
)


def test_ensure_bool() -> None:
    """Ensure bool."""
    falsey = [0, "0", "n", "no", False, "false", "nok"]
    for val in falsey:
        assert ensure_bool(val) is False
        assert ensure_bool_str(val) is False
    assert ensure_bool("") is False
    assert ensure_bool_str("") == ""

    truthy = ["yes", "1", "y", "ok", 1]
    for val in truthy:
        assert ensure_bool(val) is True
        assert ensure_bool_str(val) is True
    assert ensure_bool(100) is True
    assert ensure_bool_str(100) == "100"


def test_ensure_date() -> None:
    """Test date."""
    tests = (
        (
            "2022-10-07T09:49:03.009000",
            datetime(
                year=2022,
                month=10,
                day=7,
                hour=9,
                minute=49,
                second=3,
                microsecond=9000,
            ),
        ),
        (
            "2022-10-07T09:49:03",
            datetime(year=2022, month=10, day=7, hour=9, minute=49, second=3),
        ),
        (
            "2022-10-07T09:49:03.009000+0:00",
            datetime(
                year=2022,
                month=10,
                day=7,
                hour=9,
                minute=49,
                second=3,
                microsecond=9000,
            ),
        ),
        ("2022-10-07T09:49:03.009000a", None),
    )
    for test in tests:
        assert ensure_datetime(test[0]) == test[1]
        if test[1]:
            tzt = test[1].replace(tzinfo=timezone.utc)
            assert ensure_instant(test[0]).py_datetime() == tzt

    assert ensure_datetime("2022-10-07T09:49:03.009000") == datetime(
        year=2022, month=10, day=7, hour=9, minute=49, second=3, microsecond=9000
    )

    assert ensure_datetime("2022-10-07T09:49:03") == datetime(
        year=2022, month=10, day=7, hour=9, minute=49, second=3
    )

    assert ensure_datetime("2022-10-07T09:49:03.009000+0:00") == datetime(
        year=2022, month=10, day=7, hour=9, minute=49, second=3, microsecond=9000
    )

    assert ensure_datetime("2022-10-07T09:49:03.009000a") is None


def test_ensure_list() -> None:
    """Test ensure list."""
    assert ensure_list(None) == []
    assert ensure_list(["a"]) == ["a"]
    assert ensure_list("a") == ["a"]
    assert ensure_list('["a"]') == ["a"]
    assert ensure_list("a,b") == ["a", "b"]
    assert ensure_list("a; b") == ["a", "b"]
    assert ensure_list("a; b; b") == ["a", "b", "b"]
    assert ensure_list("a; b; b; ;") == ["a", "b", "b"]
    assert ensure_list("a/ b\n b. ;") == ["a", "b", "b."]
    assert ensure_list("a; b; b") == ["a", "b", "b"]

    assert ensure_list(None) == []
    assert ensure_list([]) == []
    assert ensure_list({}) == []
    assert ensure_list(0) == [0]
    assert ensure_list("") == []
    assert ensure_list("", delim=None) == [""]
    assert ensure_list(1) == [1]
    assert ensure_list("1") == ["1"]
    assert ensure_list(["1", 2]) == ["1", 2]

    assert ensure_list(["1", [2, "3"]], recurse=3) == ["1", 2, "3"]


def test_ensure_list_iter() -> None:
    """generators."""
    dct = {"a": 1, "b": 2}
    with pytest.raises(TypeError):
        ensure_list(dct)
    assert ensure_list(dct.keys()) == ["a", "b"]
    assert ensure_list(dct.values()) == [1, 2]


def ensure_list_json() -> None:
    assert ensure_list('["a",1]') == ["a", 1]


# def test_ensure_list_long() -> None:
#     """Ensure list."""
#     assert len(TOO_LONG) > 32000
#     res = ensure_list(TOO_LONG)
#     assert isinstance(res, list)
#     for row in res:
#         row["changes"] = {}
#     assert res == [
#         {
#             "by": "kellerza@gmail.com",
#             "changes": {},
#             "date": "2025-01-22 07:39:20.172Z",
#         }
#     ]


def test_ensure_list_with_datetime() -> None:
    res = ensure_list(
        "[{'by': 'kellerza@gmail.com', 'date': "
        "datetime.datetime(2023, 1, 13, 10, 38, 22), 'changes': "
        "{'business_value': '<s>0.000001</s><b>0.001</b>', 'priority': "
        "'<b>P3</b>', 'cse': '<b>kellerza@gmail.com</b>'} }]"
    )
    assert len(res) == 1
    assert res[0]["date"] == Instant.from_utc(2023, 1, 13, 10, 38, 22).format_rfc3339()


def test_ensure_string() -> None:
    """Test ensure string."""
    assert ensure_string(["A", "C", "B"]) == "A, C, B"
    assert ensure_string(["A", "C", "B"], sort=True) == "A, B, C"
    assert ensure_string([None, "C", "B"], sort=True) == "B, C"
    assert ensure_string(["", "C", "B"], sort=True) == "B, C"
    assert ensure_string("ABC") == "ABC"
    assert ensure_string([1, True, None]) == "1, True"
