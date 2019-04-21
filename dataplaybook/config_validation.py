"""Data validation helpers for voluptuous."""
import logging
import os
import re
from collections import OrderedDict
from typing import Any, Sequence, TypeVar, Union
from contextlib import contextmanager

import attr
import voluptuous as vol

from dataplaybook.templates import (  # noqa pylint:disable=unused-import
    isjmespath, process_templates)

# typing typevar
T = TypeVar('T')  # pylint: disable=invalid-name
RE_SLUGIFY = re.compile(r'[^a-z0-9_]+')
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


@attr.s(slots=True)
class Env():
    """Environment global variable."""
    tables = attr.ib(default=[])
    cols = attr.ib(default=[])
    lasttable = attr.ib(default='')
    env = attr.ib(default=None)

    @contextmanager
    def environment(self, env):
        """Context manager to set the environment."""
        self.env = env
        try:
            yield env
        finally:
            self.env = None

    @property
    def runtime(self):
        """Is environment set?"""
        return self.env is not None


ENV = Env()


class AttrDict(dict):
    """Simple recursive read-only attribute access (i.e. Munch)."""

    def __getattr__(self, key):
        value = self[key]
        return AttrDict(value) if isinstance(value, dict) else value

    def __setattr__(self, key, value):
        raise IOError('Read only')

    def __repr__(self):
        lst = [("{}='{}'" if isinstance(v, str) else "{}={}").format(k, v)
               for k, v in self.items()]
        return '(' + ', '.join(lst) + ')'


def AttrDictSchema(  # pylint: disable=invalid-name
        schema: dict, *post, pre=None, extra=vol.PREVENT_EXTRA) -> str:
    """Voluptuous schema that will convert dict to an AttrDict object.

    Append/pre and prepend/post validators for the complete dictionary:
    - pre: can be used for deprecation.
    - post: can be used for validators involving multiple keys."""
    if not isinstance(schema, (dict, OrderedDict)):
        raise TypeError(f"Invalid dictionary: {schema}")
    pre = ensure_list(pre)
    return vol.All(*pre, vol.Schema(schema, extra=extra),
                   lambda d: AttrDict(d), *post)  # pylint: disable=W0108


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


def table_use(value):
    """Check if valid table and already exists."""
    # value = slug(value)
    if value not in ENV.tables:
        raise vol.Invalid("Table {} does not exist".format(value))
    ENV.lasttable = value
    return value


def table_add(value):
    """Check if valid table and add to the list."""
    # value = slug(value)
    ENV.tables.append(value)
    ENV.lasttable = value
    return value


def _col(value, table=None):
    if value is None:
        raise vol.Invalid("Empty column name")
    if table is None and '.' in value:
        table, _, value = value.partition('.')
    # value = slug(value)
    if table is None:
        table = ENV.lasttable
    fullname = "{}.{}".format(table, value)
    return fullname


def col_add(value, table=None):
    """Check if valid table and add to the list."""
    fullname = _col(value, table)
    ENV.cols.append(fullname)
    _LOGGER.debug('Added col %s', fullname)
    return value


def col_copy(table_from, table_to):
    """Copy olumns from one table to another."""
    table_from = table_from + '.'
    table_to = table_to + '.'
    for col in list(ENV.cols):
        if col.startswith(table_from):
            ENV.cols.append(col.replace(table_from, table_to))


def col_use(value, table=None):
    """Ensure a column is available for use."""
    fullname = _col(value, table)
    if fullname not in ENV.cols:
        _LOGGER.warning("Column %s might not exist", fullname)
    return value


def table_remove(value):
    """Check if valid&existing table and remove from the list."""
    value = table_use(value)
    ENV.tables.remove(value)
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


def deprecate_key(key, msg, renamed=None):
    """Indicate a key is deprecated: dropped or renamed."""
    def _validator(config):
        nonlocal key
        if isinstance(key, tuple):
            conf = config[key[0]]
            key = key[1]
        else:
            conf = config

        if key not in conf:
            return config

        old_val = conf.pop(key)
        if renamed:
            nonlocal msg
            msg = f"{msg}: {key} was renamed to f{renamed}."
            if conf[renamed] in conf:
                raise vol.Invalid("{msg} {renamed} is also in the config.")
            conf[renamed] = old_val
            _LOGGER.warning(msg)
        else:
            _LOGGER.warning(
                "%s: %s was deprecated and can be removed.", msg, key)
        return config
    return _validator


def templateSchema(  # pylint: disable=invalid-name
        *schema, pre=None, runtime_only=None):
    """Template schema validator using vol.All.

    Templates are validated during startup and expanded during runtime."""
    pre = ensure_list(pre)
    runtime_only = ensure_list(runtime_only)

    def _validator(value):
        if ENV.runtime:
            return vol.All(*pre,
                           lambda t: process_templates(t, ENV.env),
                           *schema, *runtime_only)(value)
        return vol.All(*pre, process_templates, *schema)(value)

    return _validator


def task_schema(  # pylint: disable=invalid-name
        schema: dict, *additional_validators: callable,
        tables: int = 0, target: bool = False, columns: int = 0,
        kwargs=False, pre_validator=None):
    """Decorate a task_ function and add schema and kwargs.

    schema: user define schema
    additional_validators: Use to validate the entire dictionary
    tables: The count of tables sent to the function, can be tuple (min, max)
    columns: The count of columns, typically of the first table. Tuple allowed
    target: The target key/table name in the environment (Dataplaybook.tables)
    kwargs: send the options dict to the function as kwargs (**) instead of opt
    """
    if isinstance(tables, (tuple, list)):
        assert len(tables) == 2
    else:
        tables = (tables, tables)

    if columns != 0:
        if isinstance(columns, (tuple, list)):
            assert len(columns) == 2
        else:
            columns = (columns, columns)
        schema[vol.Required('columns')] = vol.All(
            ensure_list, vol.Length(min=columns[0], max=columns[1]), [str])

    the_schema = AttrDictSchema(schema)

    def _deco(func):
        """Add decorator to function, used by Task()."""
        setattr(func, 'task_schema', (
            the_schema, target, tables, kwargs,
            pre_validator, additional_validators))
        return func

    return _deco
