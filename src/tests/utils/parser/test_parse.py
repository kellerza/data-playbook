"""Test the parser."""

import logging
from dataclasses import dataclass, field
from typing import Any

from dataplaybook.utils.parser import BaseClass, parse, pre_process

_LOG = logging.getLogger(__name__)


def test_parser_alt() -> None:
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


def test_parser_false() -> None:
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


def test_parser_combine_lists() -> None:
    """Test _combine_lists."""
    assert parse._combine_lists([1, 2, 3]) == [1, 2, 3]
    assert parse._combine_lists([[1, 2], [3, 4], 5]) == [1, 2, 3, 4, 5]
    assert parse._combine_lists([None, [], []]) == []
    assert parse._combine_lists(["", None]) is None
    assert parse._combine_lists(["", None, False]) is False


def ensure_ok(val: str | bool | None) -> str:
    """Ensure the value is ok."""
    if val in (False,):
        return "no"
    if val in (True, "yes"):
        return "ok"
    if val is None:
        return ""
    return str(val)


def test_parser_false_values() -> None:
    """Test parser false values."""
    assert ensure_ok("no") == "no"
    assert ensure_ok(False) == "no"
    assert ensure_ok("") == ""

    step = parse.create_step(ensure_ok)
    assert step("ok", {"ok": False}) == "no"
    assert step("ok", {"ok": "no"}) == "no"
    assert step("ok", {"ok": ""}) == ""

    parser = parse.Parser({"ok": step})
    assert parser({"ok": "no"})[0] == {"ok": "no"}
    assert parser({"ok": False})[0] == {"ok": "no"}
    assert parser({"ok": ""})[0] == {"ok": ""}

    parser2 = parse.Parser({"ok2": parse.create_step(ensure_ok, alt=("ok",))})
    assert parser2({"ok": "no"})[0] == {"ok2": "no"}
    assert parser2({"ok": False})[0] == {"ok2": "no"}
    assert parser2({"ok": ""})[0] == {"ok2": ""}

    @pre_process(unknown_field="extra", parser=parser)
    @dataclass
    class T1(BaseClass):
        """Test class."""

        ok: str = ""
        extra: dict[str, Any] = field(default_factory=dict)

    @pre_process(unknown_field="extra", parser=parser2)
    @dataclass
    class T2(BaseClass):
        """Test class."""

        ok: str = ""
        extra: dict[str, Any] = field(default_factory=dict)

        def __post_init__(self) -> None:
            self.ok = self.extra.pop("ok2")

    assert T1.structure({"ok": "no"}) == T1(ok="no")
    assert T1.structure({"ok": False}) == T1(ok="no")
    assert T1.structure({"ok": ""}) == T1(ok="")

    assert T2.structure({"ok": "no"}) == T2(ok="", extra={"ok2": "no"})
    assert T2.structure({"ok": False}) == T2(ok="", extra={"ok2": "no"})
    assert T2.structure({"ok": ""}) == T2(ok="", extra={"ok2": ""})

    parser3 = parse.Parser({"ok2": parse.create_step(alt=("ok",))})

    assert parser3({"ok": "no"})[0] == {"ok2": "no"}
    assert parser3({"ok": False})[0] == {"ok2": False}

    @pre_process(unknown_field="extra", parser=parser3)
    @dataclass
    class T3(BaseClass):
        """Test class."""

        ok: str = ""
        extra: dict[str, Any] = field(default_factory=dict)

        def __post_init__(self) -> None:
            self.ok = ensure_ok(self.extra.get("ok2"))

    assert T3.structure({"ok": "no"}) == T3(ok="no", extra={"ok2": "no"})
    assert T3.structure({"ok": False}) == T3(ok="no", extra={"ok2": False})
