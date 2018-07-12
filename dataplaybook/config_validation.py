"""Data validation helpers for voluptuous."""
import logging
import os
import re
from collections import OrderedDict
from typing import Any, Sequence, TypeVar, Union

import voluptuous as vol

# typing typevar
T = TypeVar('T')
RE_SLUGIFY = re.compile(r'[^a-z0-9_]+')
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


class AttrDict(dict):
    """Simple recursive read-only attribute access (i.e. Munch)."""

    def __getattr__(self, key):
        value = self[key]
        return AttrDict(value) if isinstance(value, dict) else value

    def __setattr__(self, key, value):
        raise NotImplementedError

    def __repr__(self):
        lst = [("{}='{}'" if isinstance(v, str) else "{}={}").format(k, v)
               for k, v in self.items()]
        return '(' + ', '.join(lst) + ')'


def dict_schema(value: dict, *more) -> str:  # pylint: disable=invalid-name
    """Voluptuous schema that will convert dict to a Munch object."""
    if not isinstance(value, (dict, OrderedDict)):
        raise vol.DictInvalid("Invalid dictonary")
    return vol.All(vol.Schema(value),
                   lambda a: AttrDict(a), *more)  # pylint: disable=W0108


def isfile(value: Any) -> str:
    """Validate that the value is an existing file."""
    if value is None:
        raise vol.Invalid('None is not file')
    file_in = os.path.expanduser(str(value))

    if not os.path.isfile(file_in):
        raise vol.Invalid('not a file')
    if not os.access(file_in, os.R_OK):
        raise vol.Invalid('file not readable')
    return file_in


TABLES = []
LASTTABLE = ""
COLS = []


def table_use(value):
    """Check if valid table and already exists."""
    # value = slug(value)
    if value not in TABLES:
        raise vol.Invalid("Table {} does not exist".format(value))
    global LASTTABLE
    LASTTABLE = value
    return value


def table_add(value):
    """Check if valid table and add to the list."""
    # value = slug(value)
    TABLES.append(value)
    global LASTTABLE
    LASTTABLE = value
    return value


def _col(value, table=None):
    if value is None:
        raise vol.Invalid("Empty column name")
    if table is None and '.' in value:
        table, _, value = value.partition('.')
    # value = slug(value)
    if table is None:
        table = LASTTABLE
    fullname = "{}.{}".format(table, value)
    return fullname


def col_add(value, table=None):
    """Check if valid table and add to the list."""
    fullname = _col(value, table)
    COLS.append(fullname)
    _LOGGER.debug('Added col %s', fullname)
    return value


def col_copy(table_from, table_to):
    """Copy olumns from one table to another."""
    table_from = table_from + '.'
    table_to = table_to + '.'
    for col in list(COLS):
        if col.startswith(table_from):
            COLS.append(col.replace(table_from, table_to))


def col_use(value, table=None):
    """Ensure a column is available for use."""
    fullname = _col(value, table)
    if fullname not in COLS:
        _LOGGER.warning("Column %s might not exist", fullname)
    return value


def table_remove(value):
    """Check if valid&existing table and remove from the list."""
    value = table_use(value)
    TABLES.remove(value)
    return value


def slug(value):
    """Validate value is a valid slug."""
    if value is None:
        raise vol.Invalid('Slug should not be None')
    value = str(value)
    slg = util_slugify(value)
    if value == slg:
        return value
    raise vol.Invalid('invalid slug {} (try {})'.format(value, slg))


def ensure_list_csv(value: Any) -> Sequence:
    """Ensure that input is a list or make one from comma-separated string."""
    if isinstance(value, str):
        return [member.strip() for member in value.split(',')]
    return ensure_list(value)


def ensure_list(value: Union[T, Sequence[T]]) -> Sequence[T]:
    """Wrap value in list if it is not one."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def util_slugify(text: str) -> str:
    """Slugify a given text."""
    # text = normalize('NFKD', text)
    text = text.lower()
    text = text.replace(" ", "_")
    # text = text.translate(TBL_SLUGIFY)
    text = RE_SLUGIFY.sub("", text)

    return text


def endswith(parts):
    """Ensure a string ends with specified part."""
    def _check(_str):
        """Return the validator."""
        if _str.endswith(parts):
            return _str
        raise vol.Invalid('{} does not end with {}'.format(_str, parts))
    return _check


def task_schema(  # pylint: disable=invalid-name
        new: dict, *more_schema: dict,
        tables: int = 0, target: bool = False, columns: int = 0,
        kwargs=False):
    """Return a schema based on the base task schame."""
    base = OrderedDict({
        vol.Required('task'): slug,
        vol.Optional('debug*'): vol.Coerce(str),
        vol.Optional('tasks*'): vol.All(ensure_list, [dict])
    })

    if tables is not 0:
        if isinstance(tables, (tuple, list)):
            _len = vol.Length(min=tables[0], max=tables[1])
        else:
            _len = vol.Length(min=tables, max=tables)
        base[vol.Required('tables')] = vol.All(ensure_list, _len, [table_use])

    if target:
        base[vol.Required('target')] = table_add

    if columns is not 0:
        if isinstance(columns, (tuple, list)):
            _len = vol.Length(min=columns[0], max=columns[1])
        else:
            _len = vol.Length(min=columns, max=columns)
        base[vol.Required('columns')] = vol.All(
            ensure_list, _len, [str])  # was slug

    for key, val in new.items():
        base[key] = val

    the_schema = dict_schema(base, *more_schema)

    def _deco(func):
        func.schema = the_schema
        func.kwargs = kwargs
        return func

    return _deco
