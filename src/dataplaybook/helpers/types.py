"""Type helpers"""

import typing as t
from inspect import signature

import typeguard

from dataplaybook.const import Tables


def repr_signature(func: t.Callable | None, /) -> str:
    """Represent the signature."""
    if func is None:
        return "None"
    sig = str(signature(func))
    sig = (
        sig.replace("typing.", "")
        .replace("Generator[dict[str, Any], NoneType, NoneType]", "RowDataGen")
        .replace("dict[str, Any]", "RowData")
        .replace(str(Tables).replace("typing.", ""), "Tables")
    )
    sig = sig.replace("dataplaybook.helpers.env.DataEnvironment", "DataEnvironment")
    # sig = sig.replace(str(TableXXX).replace("typing.", ""), "Table")
    return sig


def _repr(a: t.Any) -> str:
    """Represent the argument."""
    res = repr(a)
    if len(res) < 50:
        return res
    return f"{res[:30]}...{res[-20:]}"


def repr_call(
    func: t.Callable, /, args: tuple | None = None, kwargs: dict | None = None
) -> str:
    """Represent the caller."""
    type_hints = t.get_type_hints(func)
    repr_args = [_repr(a) for a in args] if args else []
    repr_kwargs = [f"{k}={_repr(v)}" for k, v in kwargs.items()] if kwargs else []
    res = f"{func.__name__}({', '.join(repr_args + repr_kwargs)})"
    if "return" in type_hints:
        res = f"_ = {res}"
    return res


def check_types(
    func: t.Callable,
    /,
    args: tuple | None = None,
    kwargs: dict | None = None,
    retval: t.Any = None,
) -> None:
    """Check types."""

    call_memo = typeguard._CallMemo(func, args=args or tuple(), kwargs=kwargs or {})  # pylint: disable=protected-access
    if retval is None:
        typeguard.check_argument_types(call_memo)
    else:
        typeguard.check_return_type(retval, call_memo)
