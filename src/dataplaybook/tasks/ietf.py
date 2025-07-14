"""Telecoms related tasks."""

from __future__ import annotations
import logging
import re
from collections.abc import Callable, Generator
from re import Match
from typing import Any

import attrs

from dataplaybook import RowData, RowDataGen, task

_LOGGER = logging.getLogger(__name__)


@attrs.define()
class Standard:
    """Standard data."""

    rex: re.Pattern
    sub: str | None = None
    match: Callable[[Match], KeyStr] | None = None

    def __attrs_post_init__(self) -> None:
        """Post init."""
        if self.sub and self.match:
            raise ValueError("Cannot set both sub and match for a Standard")

    def __call__(self, match: Match) -> KeyStr:
        """Return the standard from the match."""
        s = match.start()
        if self.match:
            res = self.match(match)
            res.start = s
            return res

        if self.sub:
            return KeyStr(match.expand(self.sub), start=s)

        try:
            return KeyStr(match[1], match[2 if self.rex.groups > 1 else 1], start=s)
        except IndexError as err:
            raise ValueError(f"Check Regex {self.rex.pattern}: {err}") from err


def _re_rfc(match: Match) -> KeyStr:
    template = r"RFC\1"
    if len(match.group(1)) < 4:
        template = r"RFC" + r"\1".zfill(6 - len(match.group(1)))
    return KeyStr(match.expand(template), start=match.start())


def _re_proto(match: Match) -> KeyStr:
    key = match.group(2).lower()
    ver = match.group(3)
    if ver is None:
        return KeyStr(key, start=match.start())
    return KeyStr(f"{key} version {ver}", key=key, start=match.start())


def _re_af(match: Match) -> KeyStr:
    key = match.group(2).upper()
    ver = match.group(3)
    if ver is None:
        return KeyStr(key, start=match.start())
    return KeyStr(f"{key} version {ver}", key=key, start=match.start())


def _re_mfa(match: Match) -> KeyStr:
    ver = match.group(2)
    return KeyStr(f"MFA Forum {ver}", key=f"MFA Forum {ver}", start=match.start())


STANDARDS: list[Standard] = [
    Standard(re.compile(r"(?=[^-]|^)((draft(?:-\w+)+?)(?:-\d{2})?)(?!-\w|\w)", re.I)),
    Standard(
        re.compile(r"RFC\s*(\d{1,5})(?!\w)", re.I),
        match=_re_rfc,
    ),
    # IEEE 802.1ax
    Standard(
        re.compile(r"IEEE *(C?P?\d{2,5}(?:\.[0-9][0-9a-z]*){0,3})", re.I),
        sub=r"IEEE \1",
    ),
    # 802.1ax  (no IEEE)
    Standard(re.compile(r"(80\d\.[0-9][0-9a-z]{0,3})", re.I), sub=r"IEEE \1"),
    # IEEE 1588-2008
    Standard(
        re.compile(r"IEEE *(\d{3,4}(?:-([a-z]|\d){3,4}){1,3})\b", re.I),
        sub=r"IEEE \1",
    ),
    Standard(
        re.compile(
            r"ITU-T *(?:.recommendation *)?(\w\.\d+(?:\.\d+)?(?:\/[a-z]\.\d{3,4}| *appendix \w+)?)",
            re.I,
        ),
        sub=r"ITU-T \1",
    ),
    Standard(re.compile(r"(GR-\d+-\w+)( issue \d+)?", re.I)),
    # openconfig-lldp.yang version 0.1.0
    Standard(
        re.compile(
            r"((openconfig(?:-\w+)*.yang)(?: version (\d{1,3}(?:\.\d{1,3})+))?)", re.I
        ),
        match=_re_proto,
    ),
    Standard(re.compile(r"(3GPP *(?:TS *)?\d{1,3}\.\d+)( *release \d+)?", re.I)),
    Standard(re.compile(r"(3GPP *release *\d+)", re.I)),
    # IEEE8021-CFM-MIB revision 200706100000Z
    # IANA-RTPROTO-MIB revision 200009260000Z
    Standard(re.compile(r"(((?:\w+-)+mib)(?: +(revision [0-9a-z]+))?)", re.I)),
    # re.compile(r"(\w{2}-\w+-\d+\.\d+)"),
    Standard(re.compile(r"(FRF\.\d+)", re.I)),
    Standard(re.compile(r"(ANSI [a-z.0-9]{1,15})", re.I)),
    Standard(
        re.compile(r"((\w{3,7}\.proto)(?:\s+version\s+(\d+(?:\.\d)+))?)", re.I),
        match=_re_proto,
    ),
    Standard(re.compile(r"(MFA forum (\d+(?:\.\d+)+))", re.I), match=_re_mfa),
    Standard(
        re.compile(r"((AF(?:-\w+)+\.\d+)(?:\s+version\s+(\d+\.\d+))?)", re.I),
        match=_re_af,
    ),
    Standard(re.compile(r"((?:BBF) [A-Za-z]{2}-\d+(?!\w))", re.I)),  # BBF TR-x
    Standard(
        re.compile(r"(CVE[ -]*(\d{4})[ -]*(\d{4,7}))", re.I),
        match=lambda m: KeyStr(m.expand(r"CVE-\2-\3")),
    ),
]


class KeyStr(str):
    """Returns string with a key attribute."""

    @property
    def start(self) -> int:
        """Position of the match."""
        return getattr(self, "__start", 0)

    @start.setter
    def start(self, value: int) -> None:
        """Set the start position."""
        if not isinstance(value, int):
            raise TypeError(f"Start must be an integer, not {type(value)}")
        setattr(self, "__start", value)

    @property
    def key(self) -> Any:
        """Key of the string."""
        return getattr(self, "__key", self)

    def __new__(
        cls, text: str, key: str | None = None, start: int | None = None
    ) -> Any:
        """Init the string and the key."""
        res = super().__new__(cls, text)
        if key:
            if not isinstance(key, str):
                raise TypeError(f"Key must be a string, not {type(key)}")
            # if len(key) > len(text):
            #     raise ValueError(f"Key[{key}] should be shorter than value[{text}]")
            setattr(res, "__key", key)
        if start:
            setattr(res, "__start", start)

        return res


def extract_standards(val: str) -> Generator[KeyStr, None, None]:
    """Ensure it is unique."""
    match = {}
    for itm in _extract_standards(val):
        if itm in match:
            continue
        match[itm] = True
        yield itm


def extract_standards_ordered(val: str) -> list[KeyStr]:
    """Ensure sorted."""
    return sorted(extract_standards(val), key=lambda x: x.start)


def extract_one_standard(val: str) -> KeyStr | None:
    """Extract a single standard."""
    lst = extract_standards_ordered(val)
    return lst[0] if lst else None


def _extract_standards(val: str) -> Generator[KeyStr, None, None]:
    """Extract standards from a string."""
    for rex in STANDARDS:
        for match in rex.rex.finditer(val):
            yield rex(match)


@task
def extract_standards_from_table(
    *,
    table: list[RowData],
    extract_columns: list[str],
    include_columns: list[str] | None = None,
    name: str = "",
    line_offset: int = 1,
) -> RowDataGen:
    """Extract all RFCs from a table, into a new table."""
    _LOGGER.debug("Header start at line: %s", line_offset)

    for _no, row in enumerate(table, line_offset):
        base: dict[str, Any] = {"lineno": _no}
        if name:
            base["table"] = name

        for col in include_columns or []:
            base[col] = row.get(col)

        for coln in extract_columns:
            val = row.get(coln, None)
            if val:
                for match in extract_standards(val):
                    res = base.copy()
                    res["name"] = match
                    res["key"] = match.key
                    yield res


@task
def add_standards_column(
    *, table: list[RowData], columns: list[str], rfc_col: str
) -> None:
    """Extract all RFCs from a table."""
    for row in table:
        val = row.get(columns[0])
        new = list(extract_standards(str(val)))
        if new:
            row[rfc_col] = ", ".join(new)
