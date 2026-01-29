"""Ensure a variable is a certain type."""

import logging
import re
from ast import literal_eval
from collections import abc
from datetime import UTC, datetime
from inspect import isgenerator
from json import JSONDecodeError, loads
from typing import Any

from icecream import ic
from typing_extensions import deprecated  # In Python 3.13 it moves to warnings
from whenever import Instant, OffsetDateTime, PlainDateTime, ZonedDateTime

_LOG = logging.getLogger(__name__)


def ensure_bool(value: Any) -> bool:
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


def ensure_bool_str(value: Any, _: type | None = None) -> bool | str:
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


@deprecated("Use ensure_naive_datetime or ensure_instant instead")
def ensure_datetime(val: Any) -> datetime | None:
    """Ensure we have a datetime."""
    return ensure_naive_datetime(val)


def ensure_naive_datetime(val: Any) -> datetime | None:
    """Ensure we have a datetime."""
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        if val.tzinfo is not None:
            return val.astimezone(tz=UTC).replace(tzinfo=None)
        return val
    res = ensure_instant(val)
    return res.to_fixed_offset().to_plain().py_datetime() if res else None


RE_DATE_YYYYMMDD = re.compile(r"(20[1-3]\d)-?([01]\d)-?([0-3]\d)")
RE_DATE_MMDDYYYY = re.compile(r"([01]\d)-?([0-3]\d)-?(20[1-3]\d)")


def ensure_instant(val: Any, *, search_date: bool = False) -> Instant | None:  # noqa: PLR0911
    """Parse instant."""
    if not val:
        return None
    if isinstance(val, Instant):
        return val
    if isinstance(val, datetime):
        try:
            return Instant.from_py_datetime(val)
        except ValueError:
            # add utc if not present
            return PlainDateTime.from_py_datetime(val).assume_utc()

    if isinstance(val, str):
        val = val.strip()
        try:
            return Instant.parse_iso(val)
        except ValueError:
            pass
        try:
            return PlainDateTime.parse_iso(val).assume_utc()
        except ValueError:
            pass
        try:
            return OffsetDateTime.parse_iso(val).to_instant()
        except ValueError:
            pass
        try:
            return ZonedDateTime.parse_iso(val).to_instant()
        except ValueError:
            pass

        # Parse short date & American format
        if res := (
            RE_DATE_YYYYMMDD.search(val)
            if search_date
            else RE_DATE_YYYYMMDD.fullmatch(val)
        ):
            return Instant.from_utc(
                int(res.group(1)), int(res.group(2)), int(res.group(3))
            )
        if res := (
            RE_DATE_MMDDYYYY.search(val)
            if search_date
            else RE_DATE_MMDDYYYY.fullmatch(val)
        ):
            return Instant.from_utc(
                int(res.group(3)), int(res.group(1)), int(res.group(2))
            )

        if val.endswith("+0:00"):
            return PlainDateTime.parse_iso(val[:-5]).assume_utc()

    _LOG.warning("Could not parse date & time: %s", val)
    return None


def ensure_list[T](
    val: list[T] | tuple[T] | abc.Generator[T, None, None] | Any,
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
            return literal_eval(_format_iso(val))
        except ValueError:
            pass
        try:
            return loads(val)
        except JSONDecodeError as err:
            _LOG.warning("Invalid JSON: %s: %s", val, err.msg)
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


def _format_iso(val: str | datetime) -> str:
    """Convert a datetime() into a RFC3339 string."""
    if isinstance(val, str):
        if "datetime(" not in val:
            return val
        return re.sub(
            r"(?:datetime\.)?(datetime\([^()]+\))",
            lambda m: _format_iso(eval(m.group(1))),
            string=val,
            flags=re.I,
        )
    try:
        return f"'{Instant.from_py_datetime(val).format_iso()}'"
    except ValueError:
        return f"'{PlainDateTime.from_py_datetime(val).assume_utc().format_iso()}'"


def ensure_set(val: Any) -> set[str]:
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
