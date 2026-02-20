"""Dictionary parser for unstructured/untrusted input."""

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

type Row = dict[str, Any]
type StepFunc = Callable[[str, Row], Any]


@dataclass(slots=True)
class Parser:
    """A parser to convert a dictionary based on a recipe."""

    recipe: dict[str, StepFunc]

    def __call__(self, row: Row, in_place: bool = False) -> tuple[Row, Row]:
        """Parse the row. Returns the result & remainder."""
        res, remain = (row, row) if in_place else ({}, deepcopy(row))
        for key, step in self.recipe.items():
            val = step(key, remain)
            if val is None:
                remain.pop(key, None)
            else:
                res[key] = val
                if not in_place:
                    remain.pop(key, None)
        return res, remain


def create_step(
    convert: Callable[[Any], Any] | None = None,
    *,
    alt: tuple[str, ...] | str | None = None,
    combine: Callable[[list[Any]], Any] | None = None,
) -> StepFunc:
    """Create a step using the convert function.

    If alt is specified, the convert function should be able to handle a list.
    """
    if isinstance(alt, str):
        alt = (alt,)

    def _call(key: str, row: Row) -> Any:
        """Execute the step."""
        hasval = key in row
        val = row.get(key)

        if alt and (altv := [row.pop(v) for v in alt if v in row]):
            if hasval:
                altv.insert(0, val)
            if len(altv) == 1:
                val = altv[0]
            elif combine:
                val = combine(altv)
            else:
                val = _combine_lists(altv)

        if convert and val is not None:
            val = convert(val)

        return val

    return _call


def _combine_lists(vals: list[Any]) -> Any:
    """Check if all values in the list are lists, if so flatten."""
    haslists = any(isinstance(v, list) for v in vals)
    if haslists:
        res = list[Any]()
        for v in vals:
            if isinstance(v, list):
                res.extend(v)
            else:
                res.append(v)
        vals = res
    if vals:
        sres = set(vals)
        sres.discard(None)
        sres.discard("")
        if len(sres) < len(vals):
            vals = list(sres)
    if haslists:
        return vals
    if not vals:
        return None
    return vals[0] if len(vals) == 1 else vals


def step_remove_falsey(_: str, row: Row) -> Any:
    """Remove the field if it is falsey."""
    for rem in [key for key, val in row.items() if not val]:
        row.pop(rem)
    return None


def step_unknown_fields(key: str, row: Row) -> Any:
    """Step to generate 'extra' - extract all remaining values."""
    extra = row.pop(key, None)
    remain = {k: v for k, v in row.items() if v}
    row.clear()
    if extra:
        if not isinstance(extra, dict):
            extra = {key: extra}
        for _key, _val in extra.items():
            if val := remain.get(_key):
                if val == _val:
                    continue
                if isinstance(val, list) and _val not in val:
                    val.insert(0, _val)
                    continue
                remain[_key] = [_val, val]
                continue
            remain[_key] = _val
    if remain:
        return remain
    return None


def create_step_move_to_dict(prefix: str = "", empty: dict | None = None) -> Callable:
    """Create a step to move fields to a dict.

    Convert (ui_a:1, ui_b:2) to {ui:{a:1, b:2}}
    """

    def _call(field: str, row: dict) -> dict | None:
        """Move fields to a dict."""
        nonlocal prefix
        prefix = prefix or f"{field}_"
        ui: dict[str, Any] = row.get(field) or {}
        if not isinstance(ui, dict):
            ui = {"_": ui}
        uikeys = [k for k in row if k.startswith(prefix)]
        for uikey in uikeys:
            ui[uikey[len(prefix) :]] = row.pop(uikey)

        if not ui:
            row.pop(field, None)
            return empty
        row[field] = ui
        return ui

    return _call
