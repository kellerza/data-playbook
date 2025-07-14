"""Ensure a variable is a certain type."""

import logging
import re
import typing as t
from ast import literal_eval
from collections import abc
from datetime import datetime
from inspect import isgenerator
from json import JSONDecodeError, loads

from icecream import ic
from whenever import Instant, PlainDateTime

_LOGGER = logging.getLogger(__name__)


def ensure_bool(value: t.Any) -> bool:
    """Extract a boolean value - truthy."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if not value:
            return False
        try:
            return int(value) != 0
        except ValueError:
            pass
        if value.lower().startswith(("false", "no", "0", "n")):
            return False
        return True
    return bool(value)


def ensure_bool_str(value: t.Any, _: type | None = None) -> bool | str:
    """Extract a bool|str."""
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    lower = value.lower()
    if lower in ("false", "no", "nok", "0", "n"):
        return False
    if lower in ("true", "yes", "ok", "1", "y"):
        return True
    return value


def ensure_datetime(val: t.Any, *, silent: bool = False) -> datetime | None:
    """Ensure we have a datetime, else log it."""
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val
    if not isinstance(val, str):
        if not silent:
            _LOGGER.warning("Invalid date format '%s' (%s)", val, type(val))
        return None
    # Parse 2022-10-07T09:49:03.009000
    if val.endswith("+0:00"):
        val = val[:-5]
    try:
        return datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        pass
    try:
        return datetime.strptime(val, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError as err:
        if not silent:
            _LOGGER.warning("Invalid date '%s' (%s): %s", val, type(val), err)
    return None


def ensure_instant(val: t.Any) -> Instant | None:  # noqa: PLR0911
    """Parse instant."""
    if not val:
        return None
    if isinstance(val, Instant):
        return val
    if isinstance(val, datetime):
        try:
            return Instant.from_py_datetime(val)
        except ValueError:
            pass
        # add utc if not present
        return PlainDateTime.from_py_datetime(val).assume_utc()

    if isinstance(val, str):
        try:
            return Instant.parse_common_iso(val)
        except ValueError:
            pass
        try:
            return PlainDateTime.parse_common_iso(val).assume_utc()
        except ValueError:
            pass
        if len(val) <= 10:
            try:
                return Instant.parse_common_iso(val + " 00:00:00Z")
            except ValueError:
                pass

        return ensure_instant(ensure_datetime(val))

    raise ValueError(f"Invalid instant: {val} - {type(val)}")


T = t.TypeVar("T")


def ensure_list(  # noqa: PLR0911
    val: list[T] | tuple[T] | abc.Generator[T, None, None] | t.Any,
    *,
    recurse: int = 0,
    delim: re.Pattern | str | None = r"[\n;,/]",
) -> list:
    """Ensure val is a list."""
    if val is None:
        return []

    if recurse > 0:
        result: list = []  # type:ignore[]
        for res in ensure_list(val):
            result.extend(ensure_list(res, recurse=recurse - 1, delim=delim))
        return result

    if isinstance(val, list):
        return val
    if isinstance(val, str):
        return ensure_list_from_str(val, delim=delim)  # type:ignore[]

    if isinstance(val, dict):
        if not val:
            return []
        raise TypeError("list expected, got dict")

    if isinstance(val, abc.Iterable):
        return list(val)

    if isgenerator(val):
        return list(val)

    return [val]


def ensure_list_from_str(
    val: str, *, delim: re.Pattern | str | None = r"[\n;,/]"
) -> list[str]:
    """Ensure list with a str source."""
    if val.startswith("[") and val.endswith("]"):
        try:
            return literal_eval(_format_common_iso(val))
        except ValueError:
            pass
        try:
            return loads(val)
        except JSONDecodeError as err:
            _LOGGER.warning("Invalid JSON: %s: %s", val, err.msg)
    if val.startswith("[") and len(val) > 32000:
        rpos = val.rfind("}")
        res = val
        while rpos > 0:
            res = res[: rpos + 1] + "]"
            ic(rpos, res[-10:])
            try:
                return ensure_list(res)
            except SyntaxError:
                rpos = res.rfind("}", 0, rpos)

        raise SyntaxError("String too long")

    if delim is None:
        return [val]
    if isinstance(delim, str):
        delim = re.compile(delim)
    lst = (s.strip() for s in delim.split(val))
    return [s for s in lst if s]


def _format_common_iso(val: str | datetime) -> str:
    """Convert a datetime() into a RFC3339 string."""
    if isinstance(val, str):
        if "datetime(" not in val:
            return val
        return re.sub(
            r"(?:datetime\.)?(datetime\([^()]+\))",
            lambda m: _format_common_iso(eval(m.group(1))),
            string=val,
            flags=re.I,
        )
    try:
        return f"'{Instant.from_py_datetime(val).format_common_iso()}'"
    except ValueError:
        return (
            f"'{PlainDateTime.from_py_datetime(val).assume_utc().format_common_iso()}'"
        )


def ensure_set(val: t.Any) -> set[str]:
    """Ensure a set."""
    return val if isinstance(val, set) else set(ensure_list(val))


def ensure_string(
    value: str | list | set | int | None, *, separator: str = ", ", sort: bool = False
) -> str:
    """Combine lists and ensure field is a string."""
    if value is None:
        return ""
    if isinstance(value, list | set):
        new_list = [
            s.strip() if isinstance(s, str) else str(s)
            for s in value
            if s is not None and s != ""
        ]
        if sort:  # remove duplicates & sort - dict insertion ordered
            new_list = sorted(dict.fromkeys(new_list))
        return separator.join(new_list)
    return value if isinstance(value, str) else str(value)
