"""Read helpers."""
import logging
import os
from collections import OrderedDict


import attr
import openpyxl
import voluptuous as vol

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


@attr.s()
class Mylist(list):
    """List with additional attributes."""

    header = attr.ib()


def read_excel_deprecate(conf):
    """Change schema."""
    msg = "read_excel: Deprecated config. "
    conf_re = conf['read_excel']
    old = [k for k in conf_re if k in ('sheet', 'header', 'columns', 'target')]
    if not old:
        if 'target' in conf:
            _LOGGER.warning(
                "%s Moving 'target:' to 'read_excel.default_sheet:'", msg)
            conf_re['default_sheet'] = conf.pop('target')
        return conf
    if 'sheets' in conf_re:
        raise vol.Invalid(f"{msg} Replacement key 'sheets' also in config.")
    new = {'target': conf.pop('target', None)}
    new['name'] = conf_re.pop('sheet', None)
    new['header'] = conf_re.pop('header', 0)
    new['columns'] = conf_re.pop('columns', None)
    conf_re['sheets'] = [new]
    _LOGGER.warning(
        "%s Old keys: %s. Replace with 'sheets: [%s]'", msg, old, new)
    return conf


@cv.task_schema({
    vol.Required('file'): str,
    vol.Exclusive('sheets', 'XOR'): [vol.Schema({
        vol.Optional('name', default=None): vol.Any(str, None),
        vol.Optional('header', default=0): int,
        vol.Optional('columns', default=None): vol.Any(None, vol.Schema({
            cv.col_add: dict
        })),
        vol.Required('target'): cv.table_add,
    })],
    vol.Exclusive('default_sheet', 'XOR'): str,
}, kwargs=True, pre_validator=read_excel_deprecate)
def task_read_excel(tables, file, sheets, default_sheet=None):
    """Read excel file using openpyxl."""

    wbk = openpyxl.load_workbook(file, read_only=True, data_only=True)
    _LOGGER.debug("Loaded workbook %s.", file)

    if default_sheet:
        tables[default_sheet] = _sheet_read(wbk.active)
    for sht in sheets:
        name = sht.get('name', None) or sht['target']
        tables[sht['target']] = _sheet_read(
            wbk[name], sht.get('columns', None), sht.get('header', None))


def _sheet_read(_sheet, columns=None, header=0):
    """Read a sheet and return a table."""
    res = Mylist(header=header+2)
    res.extend(_sheet_yield_rows(_sheet, columns, header))
    _LOGGER.debug("Read %s rows from sheet %s", len(res), _sheet.title)
    return res


def _sheet_yield_rows(_sheet, columns=None, header=0):
    """Read the sheet and yield the rows."""
    rows = _sheet.rows
    while header > 0:
        next(rows)
        header -= 1
    header_row = [cell.value for cell in next(rows)]
    _LOGGER.debug("Header row: %s", header_row)
    if columns:
        _map = []  # idx, nme, val
        for nme, val in columns.items():
            fromc = str(val['from'])
            if fromc not in header_row:
                raise ValueError("{} not found in header {}".format(
                    fromc, list(header_row)))
            _map.append((list(header_row).index(fromc), nme, val))

        def _map_on_row(row):
            for idx, key, _ in _map:
                yield key, row[idx]

    for row in rows:
        record = {}
        gen = _map_on_row(row) if columns else zip(header_row, row)
        for key, cell in gen:
            if cell.data_type == 's':
                record[key] = cell.value.strip()
            else:
                record[key] = cell.value
        yield record


def get_filename(filename):
    """Get a filename to write to."""
    try:
        if os.path.isfile(filename):
            os.remove(filename)
        return filename
    except OSError:  # Open in Excel?
        _parts = list(os.path.splitext(filename))
        _parts[0] += ' '
        for idx in range(50):
            newname = str(idx).join(_parts)
            if not os.path.isfile(newname):
                _LOGGER.warning(
                    "File %s locked, saving as %s", filename, newname)
                return newname
        raise


@cv.task_schema({
    vol.Required('file'): cv.endswith('.xlsx'),
    vol.Optional('include'): vol.All(cv.ensure_list, [cv.table_use]),
    vol.Optional('header', default=[]): vol.All(cv.ensure_list, [str]),
}, kwargs=True, pre_validator=cv.deprecate_key(
    ('write_excel', 'ensure_string'), 'In function write_excel'))
def task_write_excel(
        tables, file, include=None, header=None, ensure_string=None):
    """Write an excel file."""
    header = header or []
    wbk = openpyxl.Workbook()

    if not include:
        include = list(tables.keys())

    # Remove default sheet
    wbk.remove(wbk['Sheet'])

    for table_name in include:
        wsh = wbk.create_sheet(table_name)

        if table_name not in tables:
            _LOGGER.warning("Could not save table %s", table_name)
            continue

        hdr = OrderedDict()
        for _hdr in header:
            hdr[_hdr] = 1
        for row in tables[table_name]:
            for _hdr in row.keys():
                hdr[str(_hdr)] = 1
        hdr = list(hdr.keys())
        wsh.append(hdr)

        debugs = 2
        for row in tables[table_name]:
            erow = [
                str(v) if isinstance(v, (list, dict, tuple)) or callable(v)
                else v for v in map(row.get, hdr)]
            try:
                wsh.append(erow)
            except ValueError as exc:
                wsh.append([str(row.get(h, "")) for h in hdr])
                debugs -= 1
                if debugs > 0:
                    _LOGGER.warning("Error writing %s, hdrs: %s - %s",
                                    list(erow), hdr, exc)
        if debugs < 0:
            _LOGGER.warning("Total %s errors", 2-debugs)

    wbk.save(get_filename(file))  # Write to disk
