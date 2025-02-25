"""List operations."""

import re

from dataplaybook.utils import extract_pattern, strip, unique


def test_extract_pattern() -> None:
    rex = re.compile(r"a(\d+)")
    sss, lst = extract_pattern("a1 x a2 a3 z", rex)
    assert sss == "x z"
    assert lst == [("a1", "1"), ("a2", "2"), ("a3", "3")]


def test_strip() -> None:
    """Strip spaces etc."""
    assert strip([" a", "   "]) == ["a"]
    assert strip(["a", "a"]) == ["a"]
    assert strip(["a", "b"]) == ["a", "b"]
    assert strip(["a", " b", "a"]) == ["a", "b"]
    assert strip(["a", "b", "c", "b    "]) == ["a", "b", "c"]
    assert strip(["“Prefix List” "]) == ['"Prefix List"']


def test_unique() -> None:
    """Test list items are unique."""
    assert unique(["a", "b", "a"]) == ["a", "b"]
    assert unique(["a"]) == ["a"]
