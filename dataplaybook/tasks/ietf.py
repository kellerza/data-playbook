"""Telecoms related tasks."""
import logging
import re
from typing import List, Optional

from dataplaybook import Columns, Table, task

_LOGGER = logging.getLogger(__name__)


REGEX = (
    re.compile(r"(?=[^-]|^)((draft-[\w-]+?)(?:-\d{2})?)-*(?![-\w])", re.I),
    (
        r"RFC\1",
        re.compile(r"RFC\s*(\d{1,5})(?:\D|$)", re.I),
    ),
    (r"IEEE \1", re.compile(r"IEEE *(\d{3,4}(?:\.\w+|\D\d)?(?:-\d{4})?)", re.I)),
    (r"IEEE \1", re.compile(r"(80[12].\d\w+)", re.I)),
    (r"ITU-T \1", re.compile(r"ITU-T *(?:recommendation *)?(\w\.\d+(?:\.\d+)?)", re.I)),
    re.compile(r"(GR-\d+-\w+)", re.I),
    re.compile(r"((openconfig(?:-\w+)*.yang)(?: version \d(?:\.\d)+)?)"),
    re.compile(r"(3GPP \w+ \d+(\.\d+)*)"),
    re.compile(r"((?:\w+-)+mib)", re.I),
    # re.compile(r"(\w{2}-\w+-\d+\.\d+)"),
    re.compile(r"(FRF[\.\d]+)"),
    re.compile(r"(ANSI \S+)"),
    re.compile(r"(gnmi(\.\w+)*)", re.I),
)


class KeyStr(str):
    """Returns string with a key attribute."""

    @property
    def start(self):
        """Position of the match."""
        return getattr(self, "__start", 0)

    @property
    def key(self):
        """The key part of the string."""
        return getattr(self, "__key", self)

    def __new__(cls, text, key=None, start=None):
        """Init the string and the key."""
        res = super().__new__(cls, text)
        if key:
            if not isinstance(key, str):
                raise TypeError("Key must be a string, not {}".format(type(key)))
            if len(key) > len(text):
                raise ValueError(
                    "Key[{}] should be shorter than value[{}]".format(key, text)
                )
            setattr(res, "__key", key)
        if start:
            setattr(res, "__start", start)

        return res


def extract_standards(val: str) -> List[str]:
    """Ensure it is unique."""
    match = {}
    for itm in _extract_standards(val):
        if itm in match:
            continue
        match[itm] = True
        yield itm


def extract_standards_ordered(val: str) -> List[str]:
    """Ensure sorted."""
    return sorted(extract_standards(val), key=lambda x: x.start)


def extract_one_standard(val: str) -> str:
    """Extract a single standard."""
    lst = extract_standards_ordered(val)
    return lst[0] if lst else None


def _extract_standards(val):
    """Extract standards from a string."""
    for rex in REGEX:
        if isinstance(rex, tuple):
            for match in rex[1].finditer(val):
                # _LOGGER.debug("%s groups: %s", rex, match.groups())
                template = rex[0]
                if template.startswith("RFC") and len(match.group(1)) < 4:
                    template = r"RFC" + r"\1".zfill(6 - len(match.group(1)))
                yield KeyStr(
                    match.expand(template),
                    match.expand(rex[2]) if len(rex) > 2 else None,
                    start=match.start(),
                )
            continue

        for match in rex.finditer(val):
            yield KeyStr(
                match[1], match[2 if rex.groups > 1 else 1], start=match.start()
            )


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
