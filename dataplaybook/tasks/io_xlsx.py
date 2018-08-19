"""Read helpers."""
import logging
import os
from collections import OrderedDict
from timeit import default_timer as timer

import attr
import openpyxl
import voluptuous as vol

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


@attr.s()
class Mylist(list):
    """List with additional attributes."""

    header = attr.ib()


@cv.task_schema({
    vol.Required('file'): str,
    vol.Optional('sheet'): str,
    vol.Optional('header'): int,
    vol.Optional('columns'): vol.Schema({
        cv.col_add: dict
    }),
}, target=1, kwargs=True)
def task_read_excel(_, file, sheet=None, header=0, columns=None):
    """Read excel file using openpyxl."""
    t_start = timer()
    wbk = openpyxl.load_workbook(file, read_only=True, data_only=True)
    t_mid = timer()

    _sheet = wbk.active if not sheet else wbk[sheet]
    rows = _sheet.rows
    data = Mylist(header=header+2)
    while header > 0:
        next(rows)
        header -= 1
    header_row = [cell.value for cell in next(rows)]
    # print(header_row)
    if columns:
        _map = []  # idx, nme, val
        for nme, val in columns.items():
            fromc = str(val['from'])
            if fromc not in header_row:
                raise ValueError("{} not found in header {}".format(
                    fromc, list(header_row)))
            _map.append((list(header_row).index(fromc), nme, val))

        # Colclass = attr.make_class(
        #    name, [nme for (_, nme, _) in _map], slots=True)

        # Colclass = namedtuple(  # pylint: disable-invalid-name
        #    name, [nme for (_, nme, _) in _map])

        for row in rows:
            record = {}  # []
            for idx, nme, val in _map:
                record[nme] = row[idx].value
                # cell = row[idx]
                # if cell.data_type == 's':
                #    # record.append(cell.value.strip())
                # else:
                #    # record.append(cell.value)
            # data.append(Colclass(*record))
            data.append(record)
    else:
        for row in rows:
            record = {}
            for key, cell in zip(header_row, row):
                if cell.data_type == 's':
                    record[key] = cell.value.strip()
                else:
                    record[key] = cell.value
            data.append(record)

    t_end = timer()
    _LOGGER.debug("read_excel({}): {:.2f}s convert: {:.2f}s"
                  .format(file, t_mid-t_start, t_end-t_mid))

    return data


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
    vol.Optional('ensure_string', []): list
}, kwargs=True)
def task_write_excel(
        tables, file, ensure_string=None, include=None, header=None):
    """Write an excel file."""
    ensure_string = ensure_string or []
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
            try:
                erow = [str(row.get(h, '')) if h in ensure_string
                        else row.get(h) for h in hdr]
                wsh.append(erow)
            except ValueError:
                wsh.append([str(row.get(h, "")) for h in hdr])
                debugs -= 1
                if debugs > 0:
                    _LOGGER.warning("Error writing %s, hdrs: %s",
                                    list(row.values()), hdr)
        if debugs < 0:
            _LOGGER.warning("Total %s errors", 2-debugs)

    wbk.save(get_filename(file))  # Write to disk
