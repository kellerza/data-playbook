"""Dictionary parser for unstructured/untrusted input."""

import typing as t
from copy import deepcopy

import attrs

type Row = dict[str, t.Any]
type StepFunc = t.Callable[[str, Row], t.Any]


@attrs.define(slots=True)
class Parser:
    """A parser to convert a dictionary based on a recipe."""

    recipe: dict[str, StepFunc]

    def __call__(self, row: Row, in_place: bool = False) -> tuple[Row, Row]:
        """Parse the row. Returns the result & remainder."""
        res, remain = (row, row) if in_place else ({}, deepcopy(row))
        for field, step in self.recipe.items():
            try:
                res[field] = step(field, remain)
            except AttributeError:
                pass
        return res, remain


def create_step(
    convert: t.Callable[[t.Any], t.Any] | None = None,
    *,
    alt: tuple[str, ...] | str | None = None,
) -> StepFunc:
    """Create a step using the convert function.

    If alt is specified, the convert function should be able to handle a list.
    """
    if isinstance(alt, str):
        alt = (alt,)

    def _call(key: str, row: Row) -> t.Any:
        """Execute the step."""
        val = row.pop(key, None)

        if not (alt and any(a in row for a in alt)):
            if not val:
                raise AttributeError
            return convert(val) if convert else val

        altvals = [av for av in (row.pop(v, None) for v in alt) if av]
        if not altvals:
            if not val:
                raise AttributeError
            return convert(val) if convert else val

        # Alt exists, try to combine with val
        if val:
            altvals.insert(0, val)

        if len(altvals) == 1:
            return convert(altvals[0]) if convert else altvals[0]

        return convert(altvals) if convert else altvals

    return _call


def step_remove_falsey(_: str, row: Row) -> t.Any:
    """Remove the field if it is falsey."""
    for rem in [key for key, val in row.items() if not val]:
        row.pop(rem)
    raise AttributeError


def step_unknown_fields(key: str, row: Row) -> t.Any:
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
    raise AttributeError


def create_step_move_to_dict(prefix: str = "", empty: dict | None = None) -> t.Callable:
    """Create a step to move fields to a dict.

    Convert (ui_a:1, ui_b:2) to {ui:{a:1, b:2}}
    """

    def _call(field: str, row: dict) -> dict | None:
        """Move fields to a dict."""
        nonlocal prefix
        prefix = prefix or f"{field}_"
        ui = row.get(field) or {}
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
