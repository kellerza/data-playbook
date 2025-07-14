"""List operations."""

import logging
import re
import typing as t
from collections import abc

L = t.TypeVar("L")
T = t.TypeVar("T", str, list, int)


def append_unique(target: list[T], source: abc.Iterable[T]) -> bool:
    """Add unique items to a list. Return True if the list was changed."""
    res = False
    for item in source:
        if item not in target:
            target.append(item)
            res = True
    return res


def extract_pattern(text: str, regex: re.Pattern) -> tuple[str, list[tuple]]:
    """Extract a pattern from regex. Returns the remainder of the text and a list of matches."""
    if not text:
        return "", []
    matches = []

    def _extract(match: re.Match) -> str:
        matches.append((match.group(0), *match.groups()))
        return ""

    text = strip(regex.sub(_extract, text), strip_doubles=True)
    return text, matches


def strip(val: T, *, strip_doubles: bool = False) -> T:
    """Strip spaces & quotes from strings, Strip duplicates & empty strings from a list."""
    if isinstance(val, str):
        res = val.strip().replace("“", '"').replace("”", '"')
        if strip_doubles and "  " in res:
            res = re.sub(r"  +", " ", res)
        return res

    if not isinstance(val, list):
        return val

    res = [strip(s) for s in val]
    try:
        dres = dict.fromkeys(res)  # dict insertion is ordered
    except TypeError as err:
        logging.getLogger(__name__).error(err, val)
        return res
    dres.pop("", None)
    dres.pop(None, None)
    return list(dres)


def unique(val: list[L]) -> list[L]:
    """Only allow unique items in the list."""
    # Since dict insertion is ordered...
    return list(dict.fromkeys(val))
