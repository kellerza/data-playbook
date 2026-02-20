"""Test the parser."""

from dataplaybook.utils.parser import parse


def test_parse_alt() -> None:
    """Test alternative item."""
    p = parse.Parser(recipe={"items": parse.create_step(alt="item")})

    res = p({"items": "i1"})[0]
    assert res == {"items": "i1"}

    res = p({"items": "i1", "item": "i2"})[0]
    assert res == {"items": ["i1", "i2"]}

    res = p({"items": [], "item": ["i2", "other"]})[0]
    assert res == {"items": ["i2", "other"]}

    res = p({"items": "", "item": ["i2"]})[0]
    assert res == {"items": ["i2"]}


def test_parse_false() -> None:
    """Test pass_false."""
    p = parse.Parser(recipe={"a": parse.create_step(alt=("b", "c"))})

    res = p({"a": "1"})[0]
    assert res == {"a": "1"}

    res = p({"a": None, "b": "2"})[0]
    assert res == {"a": "2"}

    res = p({"a": None, "b": None})[0]
    assert res == {}

    res = p({"a": False, "b": False})[0]
    assert res == {"a": False}

    res = p({"b": False, "c": False})[0]
    assert res == {"a": False}


def test_parse_combine_lists() -> None:
    """Test _combine_lists."""
    assert parse._combine_lists([1, 2, 3]) == [1, 2, 3]
    assert parse._combine_lists([[1, 2], [3, 4], 5]) == [1, 2, 3, 4, 5]
    assert parse._combine_lists([None, [], []]) == []
    assert parse._combine_lists(["", None]) is None
    assert parse._combine_lists(["", None, False]) is False
