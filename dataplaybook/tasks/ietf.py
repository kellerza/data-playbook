"""Telecoms related tasks."""
import logging
import re
from typing import Any, Generator, Match, Optional

from dataplaybook import Columns, Table, task

_LOGGER = logging.getLogger(__name__)


def _re_rfc(match: Match) -> tuple[str, Optional[str]]:
    template = r"RFC\1"
    if len(match.group(1)) < 4:
        template = r"RFC" + r"\1".zfill(6 - len(match.group(1)))
    return match.expand(template), None


def _re_proto(match: Match) -> tuple[str, Optional[str]]:
    key = match.group(2).lower()
    ver = match.group(3)
    if ver is None:
        return key, None
    return f"{key} version {ver}", key


def _re_af(match: Match) -> tuple[str, Optional[str]]:
    key = match.group(2).upper()
    ver = match.group(3)
    if ver is None:
        return key, None
    return f"{key} version {ver}", key


def _re_mfa(match: Match) -> tuple[str, Optional[str]]:
    ver = match.group(2)
    return f"MFA Forum {ver}", f"MFA Forum {ver}"


REGEX = (
    # re.compile(r"(?=[^-]|^)((draft-[\w-]+?)(?:-\d{2})?)-*(?![-\w])", re.I),
    re.compile(r"(?=[^-]|^)((draft(?:-\w+)+?)(?:-\d{2})?)(?!-\w|\w)", re.I),
    (
        _re_rfc,
        re.compile(r"RFC\s*(\d{1,5})(?!\w)", re.I),
    ),
    # IEEE 802.1ax
    (r"IEEE \1", re.compile(r"IEEE *(C?P?\d{2,5}(?:\.[0-9][0-9a-z]*){0,3})", re.I)),
    # 802.1ax  (no IEEE)
    (r"IEEE \1", re.compile(r"(80\d\.[0-9][0-9a-z]{0,3})", re.I)),
    # IEEE 1588-2008
    (
        r"IEEE \1",
        re.compile(r"IEEE *(\d{3,4}(?:-[a-z]{3,4}){1,3})", re.I),
    ),
    (
        r"ITU-T \1",
        re.compile(
            r"ITU-T *(?:.recommendation *)?(\w\.\d+(?:\.\d+)?(?:\/[a-z]\.\d{3,4}| *appendix \w+)?)",
            re.I,
        ),
    ),
    re.compile(r"(GR-\d+-\w+)( issue \d+)?", re.I),
    # openconfig-lldp.yang version 0.1.0
    (
        _re_proto,
        re.compile(
            r"((openconfig(?:-\w+)*.yang)(?: version (\d{1,3}(?:\.\d{1,3})+))?)", re.I
        ),
    ),
    re.compile(r"(3GPP *(?:TS *)?\d{1,3}\.\d+)( *release \d+)?", re.I),
    re.compile(r"(3GPP *release *\d+)", re.I),
    # IEEE8021-CFM-MIB revision 200706100000Z
    # IANA-RTPROTO-MIB revision 200009260000Z
    re.compile(r"(((?:\w+-)+mib)(?: +(revision [0-9a-z]+))?)", re.I),
    # re.compile(r"(\w{2}-\w+-\d+\.\d+)"),
    re.compile(r"(FRF\.\d+)", re.I),
    re.compile(r"(ANSI [a-z.0-9]{1,15})", re.I),
    (
        _re_proto,
        re.compile(r"((\w{3,7}\.proto)(?:\s+version\s+(\d+(?:\.\d)+))?)", re.I),
    ),
    (_re_mfa, re.compile(r"(MFA forum (\d+(?:\.\d+)+))", re.I)),
    (_re_af, re.compile(r"((AF(?:-\w+)+\.\d+)(?:\s+version\s+(\d+\.\d+))?)", re.I)),
    re.compile(r"((?:BBF) [A-Za-z]{2}-\d+(?!\w))", re.I),  # BBF TR-x
)


class KeyStr(str):
    """Returns string with a key attribute."""

    @property
    def start(self) -> int:
        """Position of the match."""
        return getattr(self, "__start", 0)

    @property
    def key(self) -> Any:
        """Key of the string."""
        return getattr(self, "__key", self)

    def __new__(
        cls, text: str, key: Optional[str] = None, start: Optional[int] = None
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


def extract_one_standard(val: str) -> KeyStr:
    """Extract a single standard."""
    lst = extract_standards_ordered(val)
    return lst[0] if lst else None


def _extract_standards(val) -> Generator[KeyStr, None, None]:
    """Extract standards from a string."""
    for rex in REGEX:
        if isinstance(rex, tuple):
            for match in rex[1].finditer(val):
                # _LOGGER.debug("%s groups: %s", rex, match.groups())
                if callable(rex[0]):
                    text, key = rex[0](match)
                    yield KeyStr(text, key=key, start=match.start())
                    continue

                yield KeyStr(
                    match.expand(rex[0]),
                    match.expand(rex[2]) if len(rex) > 2 else None,
                    start=match.start(),
                )
            continue

        for match in rex.finditer(val):
            try:
                yield KeyStr(
                    match[1], match[2 if rex.groups > 1 else 1], start=match.start()
                )
            except IndexError as err:
                _LOGGER.error("Check Regex %s: %s", rex, err)


@task
def extract_standards_from_table(
    table: Table, extract_columns: Columns, include_columns: Optional[Columns] = None
) -> Table:
    """Extract all RFCs from a table, into a new table."""
    header = getattr(table, "header", 1)
    name = getattr(table, "name", "")
    _LOGGER.debug("Header start at line: %s", header)

    for _no, row in enumerate(table, header):
        base = {"lineno": _no}
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
def add_standards_column(table: Table, columns: Columns, rfc_col: str):
    """Extract all RFCs from a table."""
    for row in table:
        val = row.get(columns[0])
        new = list(extract_standards(val))
        if new:
            row[rfc_col] = ", ".join(new)
