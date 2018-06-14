"""Telecoms related tasks."""
import logging
import re

import voluptuous as vol

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


RE_DRAFT = re.compile(r"[^-](draft(?:-\w+)+?)(-\d{2})?[^-]")
RE_RFC = re.compile(r"RFC\s*(\d{3,5})\D")


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
                for match in RE_DRAFT.finditer(val):
                    res = base.copy()
                    res['rfc'] = match[1]
                    res['rev'] = match[2]
                    yield res
                for match in RE_RFC.finditer(val):
                    res = base.copy()
                    res['rfc'] = 'RFC' + match[1]
                    yield res


@cv.task_schema({
    vol.Required('rfc_col'): cv.col_add
}, tables=1, columns=(1))
def task_add_rfc_column(table, opt):
    """Extract all RFCs from a table."""
    for row in table:
        val = row.get(opt.columns[0])
        new = []

        for match in RE_DRAFT.finditer(val):
            new.append(match[1])

        for match in RE_RFC.finditer(val):
            new.append(match[1])

        if new:
            row[opt.rfc_col] = ', '.join(new)
