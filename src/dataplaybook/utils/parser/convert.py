"""Custom cattrs converter."""

import typing as t
from collections import abc

from cattrs import ClassValidationError, Converter, transform_error
from whenever import Instant

from ..ensure import (
    ensure_bool,
    ensure_bool_str,
    ensure_instant,
    ensure_list,
    ensure_string,
)

T = t.TypeVar("T")


CONVERT = Converter(
    forbid_extra_keys=True,
    omit_if_default=True,
    unstruct_collection_overrides={abc.Set: sorted},
)


@CONVERT.register_structure_hook  # type:ignore[]
def ensure_a_string(value: t.Any, _: type) -> str:
    """Ensure this is a string."""
    return ensure_string(value)


@CONVERT.register_structure_hook  # type:ignore[]
def ensure_a_bool(value: t.Any, _: type) -> bool:
    """Ensure this is a bool."""
    return ensure_bool(value)


def _hook_list(value: t.Any, cls: type) -> t.Any:
    """Structure a list."""
    args = t.get_args(cls)
    arg0 = args[0]
    if isinstance(value, set | list):
        return [CONVERT.structure(i, arg0) for i in value]
    return [CONVERT.structure(i, arg0) for i in ensure_list(value)]


CONVERT.register_structure_hook_func(lambda v: t.get_origin(v) is list, _hook_list)


def _hook_set(value: t.Any, cls: type) -> t.Any:
    """Structure a set."""
    args = t.get_args(cls)
    arg0 = args[0]
    if isinstance(value, set | list):
        return {CONVERT.structure(i, arg0) for i in value}
    return {CONVERT.structure(i, arg0) for i in ensure_list(value)}


CONVERT.register_structure_hook_func(lambda v: t.get_origin(v) is set, _hook_set)


def structure1(
    data: t.Any,
    cls: type[T],
    *,
    forbid_extra_keys: bool = True,
    omit_if_default: bool = True,
) -> T:
    """Structure simple values."""
    try:
        return get_converter(
            forbid_extra_keys=forbid_extra_keys, omit_if_default=omit_if_default
        ).structure(data, cls)
    except ClassValidationError as err:
        raise ValueError("; ".join(transform_error(err)))  # noqa: B904


CONVERT.register_structure_hook(bool | str, ensure_bool_str)


@CONVERT.register_structure_hook  # type:ignore[]
def int_str(value: t.Any, _: type | None = None) -> int | str:
    """Extract a int|str."""
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    try:
        return int(value)
    except ValueError:
        pass
    return value


@CONVERT.register_structure_hook  # type:ignore[]
def int_float(value: t.Any, _: type | None = None) -> int | float:
    """Extract a int|str."""
    if isinstance(value, int):
        return value
    if not isinstance(value, float):
        value = float(value)
    if int(value) == value:
        return int(value)
    return value


@CONVERT.register_structure_hook  # type:ignore[]
def int_float_none(value: t.Any, _: type | None = None) -> int | float | None:
    """Extract a int|str."""
    if value is None or value == "":
        return None
    return int_float(value)


CONVERT.register_unstructure_hook(Instant, lambda dt: dt.py_datetime())
CONVERT.register_structure_hook(Instant, lambda i, _: ensure_instant(i))


_CONVERT: dict[tuple[bool, bool], Converter] = {
    (True, True): CONVERT,
    (True, False): CONVERT.copy(omit_if_default=True, forbid_extra_keys=False),
    (False, True): CONVERT.copy(omit_if_default=False, forbid_extra_keys=True),
    (False, False): CONVERT.copy(omit_if_default=False, forbid_extra_keys=False),
}


def get_converter(
    forbid_extra_keys: bool = True, omit_if_default: bool = True
) -> Converter:
    """Get a converter with different settings. Needs to be copied before execution."""
    return _CONVERT[(omit_if_default, forbid_extra_keys)]
