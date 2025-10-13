"""Type helpers."""

from collections.abc import Callable
from inspect import signature
from typing import Any, get_type_hints

from typeguard import CollectionCheckStrategy, config

from dataplaybook.const import Tables

config.collection_check_strategy = CollectionCheckStrategy.ALL_ITEMS


def repr_signature(func: Callable | None, /) -> str:
    """Represent the signature."""
    if func is None:
        return "None"
    sig = str(signature(func))
    sig = (
        sig.replace("typing.", "")
        .replace("collections.abc.", "")
        .replace("dict[str, Any]", "RowData")
        .replace("Generator[RowData, None, None]", "RowDataGen")
        .replace(str(Tables).replace("typing.", ""), "Tables")
    )
    sig = sig.replace("dataplaybook.helpers.env.DataEnvironment", "DataEnvironment")
    # sig = sig.replace(str(TableXXX).replace("typing.", ""), "Table")
    return sig


def _repr(a: Any) -> str:
    """Represent the argument."""
    res = repr(a)
    if len(res) < 50:
        return res
    return f"{res[:30]}...{res[-20:]}"


def repr_call(
    func: Callable, /, args: tuple | None = None, kwargs: dict | None = None
) -> str:
    """Represent the caller."""
    type_hints = get_type_hints(func)
    repr_args = [_repr(a) for a in args] if args else []
    repr_kwargs = [f"{k}={_repr(v)}" for k, v in kwargs.items()] if kwargs else []
    res = f"{func.__name__}({', '.join(repr_args + repr_kwargs)})"
    if "return" in type_hints:
        res = f"_ = {res}"
    return res
