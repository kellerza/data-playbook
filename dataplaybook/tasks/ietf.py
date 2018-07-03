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
    re.compile(r"GR-\d+-\w+", re.I),
)


class Str(str):
    """String with attributes."""
    pass


def extract_rfc(val):
    """Extract standards from a string."""
    for match in RE_RFC.finditer(val):
        yield 'RFC' + match[1]
    for match in RE_IEEE.finditer(val):
        yield 'IEEE ' + match[1]
    for match in RE_ITUT.finditer(val):
        yield 'ITU-T ' + match[1].upper()
    for match in RE_DRAFT.finditer(val):
        if match[2]:
            astr = Str(match[1] + match[2])
            setattr(astr, 'draft', (match[1], match[2]))
            yield astr
        else:
            yield match[1]
    for regex in RE_OTHER:
        for match in regex.finditer(val):
            yield match[0]


@cv.task_schema({
    vol.Optional('include_columns', default=[]): vol.All(
        cv.ensure_list, [cv.col_use])
}, tables=1, columns=(1, 10), target=1)
def task_extract_rfc(table, opt):
    """Extract all RFCs from a table."""
    header = getattr(table, 'header', 1)
    _LOGGER.debug("Header start at line: %s", header)
    for _no, row in enumerate(table, header):

        base = {'table': opt.tables[0], 'lineno': _no}
        for col in opt.include_columns:
            base[col] = row.get(col)

        for coln in opt.columns:
            val = row.get(coln, None)
            if val:
                for match in extract_rfc(val):
                    res = base.copy()
                    if getattr(match, 'draft', False):
                        res['rfc'] = getattr(match, "draft")[0]
                        res['rev'] = getattr(match, "draft")[1]
                        yield res
                        continue
                    res['rfc'] = match
                    yield res


@cv.task_schema({
    vol.Required('rfc_col'): cv.col_add
}, tables=1, columns=(1))
def task_add_rfc_column(table, opt):
    """Extract all RFCs from a table."""
    for row in table:
        val = row.get(opt.columns[0])
        new = list(extract_rfc(val))
        if new:
            row[opt.rfc_col] = ', '.join(new)
