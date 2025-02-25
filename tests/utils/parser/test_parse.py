"""Test the parser."""

from dataplaybook.utils.parser import parse


def test_alt() -> None:
    p = parse.Parser(recipe={"items": parse.create_step(alt="item")})

    res = p({"items": "i1"})[0]
    assert res == {"items": "i1"}

    res = p({"items": "i1", "item": "i2"})[0]
    assert res == {"items": ["i1", "i2"]}

    res = p({"items": [], "item": ["i2", "other"]})[0]
    assert res == {"items": ["i2", "other"]}

    res = p({"items": "", "item": ["i2"]})[0]
    assert res == {"items": ["i2"]}
