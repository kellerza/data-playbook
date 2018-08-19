"""Telecoms related tasks."""
import logging
import re

import voluptuous as vol

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


RE_DRAFT = re.compile(r"(?:[^-]|^)(draft(?:-\w+)+?)(-\d{2})?(?:[^-]|$)", re.I)
RE_RFC = re.compile(r"RFC\s*(\d{3,5})(?:\D|$)", re.I)
RE_IEEE = re.compile(r"IEEE *(\d{3,4}(?:\.\w+|\D\d)?(?:-\d{4})?)", re.I)
RE_ITUT = re.compile(r"ITU-T *(?:recommendation *)?(\w\.\d+(?:\.\d+)?)", re.I)
RE_OTHER = (
    re.compile(r"(GR-\d+-\w+)", re.I),
    re.compile(r"((openconfig(?:-\w+)*.yang)(?: version \d(?:\.\d)+)?)"),
    re.compile(r"(3GPP \w+ \d+(\.\d+)+)"),
    re.compile(r"(\S+-mib)", re.I),
    re.compile(r"(\w{2}-\w+-\d+\.\d+)"),
    re.compile(r"(FRF[\.\d]+)"),
    re.compile(r"(ANSI \S+)"),
)


class KeyStr(str):
    """Returns string with a key attibute."""
    @property
    def key(self):
        return getattr(self, '__key', self)

    def __new__(cls, text, key=None):
        """Init the string and the key."""
        res = super().__new__(cls, text)
        if key:
            if not isinstance(key, str):
                raise TypeError('Key must be a string, not {}'
                                .format(type(key)))
            if len(key) > len(text):
                raise ValueError('Key[{}] should be shorter than value[{}]'
                                 .format(key, text))
            setattr(res, '__key', key)

        return res


def extract_standards(val):
    """Extract standards from a string."""
    for match in RE_RFC.finditer("RFC" + val):
        yield KeyStr('RFC' + match[1])
    for match in RE_DRAFT.finditer(val):
        if match[2]:
            yield KeyStr(match[1] + match[2], match[1])
        else:
            yield KeyStr(match[1])
    for match in RE_IEEE.finditer(val):
        yield KeyStr('IEEE ' + match[1])
    for match in RE_ITUT.finditer(val):
        yield KeyStr('ITU-T ' + match[1])
    for regex in RE_OTHER:
        for match in regex.finditer(val):
            yield KeyStr(match[1], match[2 if regex.groups > 1 else 1])


def extract_one_standard(val):
    """Extract a single standard."""
    return next(extract_standards(val), None)


@cv.task_schema({
    vol.Optional('include_columns', default=[]): vol.All(
        cv.ensure_list, [cv.col_use])
}, tables=1, columns=(1, 10), target=1)
def task_extract_standards(table, opt):
    """Extract all RFCs from a table, into a new table."""
    header = getattr(table, 'header', 1)
    _LOGGER.debug("Header start at line: %s", header)
    for _no, row in enumerate(table, header):

        base = {'table': opt.tables[0], 'lineno': _no}
        for col in opt.include_columns:
            base[col] = row.get(col)

        for coln in opt.columns:
            val = row.get(coln, None)
            if val:
                for match in extract_standards(val):
                    res = base.copy()
                    res['name'] = match
                    res['key'] = getattr(match, 'key', match)
                    yield res


@cv.task_schema({
    vol.Required('rfc_col'): cv.col_add
}, tables=1, columns=(1))
def task_add_standards_column(table, opt):
    """Extract all RFCs from a table."""
    for row in table:
        val = row.get(opt.columns[0])
        new = list(extract_standards(val))
        if new:
            row[opt.rfc_col] = ', '.join(new)
