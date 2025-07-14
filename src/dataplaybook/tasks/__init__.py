"""General tasks."""

import json
import logging
import re
import shutil
import typing as t
from collections import abc

from dataplaybook import RowData, RowDataGen, Tables, task
from dataplaybook.utils import ensure_list

_LOGGER = logging.getLogger(__name__)


@task
def build_lookup(*, table: list[RowData], key: str, columns: list[str]) -> RowDataGen:
    """Build a lookup table (unique key & columns) and removing the columns."""
    lookup: RowData = {}
    all_cols = list(columns)
    all_cols.insert(0, key)
    # _LOGGER.warning(all_cols)
    for row in table:
        if not lookup.get(row[key]):
            yield {c: row.get(c) for c in all_cols}
            lookup[row[key]] = True
        for col in columns:
            row.pop(col)


@task
def build_lookup_dict(
    *, table: list[RowData], key: str | list[str], columns: list[str] | None = None
) -> dict[str | tuple, t.Any]:
    """Build lookup tables {key: columns}."""
    lookup: dict[str | tuple, t.Any] = {}
    get_key = (
        (lambda r: r.get(key) or "")
        if isinstance(key, str)
        else (lambda r: tuple(r.get(k, "") for k in key))
    )
    for row in table:
        keyv = get_key(row)
        if keyv and not lookup.get(keyv):
            lookup[keyv] = {c: row.get(c) for c in columns} if columns else row
    return lookup


@task
def combine(
    *,
    tables: list[list[RowData]],
    key: str,
    columns: list[str],
    value: t.Literal[True] | str = True,
) -> list[RowData]:
    """Combine multiple tables on key.

    key: unique identifier for the rows
    columns: additional columns to add from the first table with the row
    target: output
    """
    _res = {}
    copy_columns = list(columns)
    copy_columns.insert(0, key)
    for table, table_name in zip(tables, columns, strict=False):
        for row in table:
            key = row[key]
            if key not in _res:
                _res[key] = {k: row.get(k, "") for k in copy_columns}
            else:
                pass  # add redundant info...
            _res[key][table_name] = True if value is True else row[value]
    return list(_res.values())


@task
def ensure_lists(
    *, tables: abc.Sequence[list[RowData]], columns: abc.Sequence[str]
) -> None:
    """Recursively run ensure_list on columns in all tables."""
    for table in tables:
        for row in table:
            for col in columns:
                if col not in row:
                    continue
                # row[col] = ensure_list(row[col])
                val = row.get(col)
                if isinstance(val, list | tuple):
                    continue
                if not val:
                    row[col] = []
                    continue
                if not isinstance(val, str):
                    _LOGGER.warning("ensure_lists: %s %s", type(val), val)
                    continue
                if val.startswith("["):
                    # try json
                    try:
                        row[col] = json.loads(val)
                        continue
                    except ValueError:
                        pass
                row[col] = ensure_list(val)


@task
def filter_rows(
    *,
    table: list[RowData],
    include: dict[str, str] | None = None,
    exclude: dict[str, str | list[str] | re.Pattern] | None = None,
) -> RowDataGen:
    """Filter rows from a table."""

    def _match(
        criteria: dict[str, str] | dict[str, str | list[str] | re.Pattern], row: RowData
    ) -> bool:
        """Test if row matches criteria [OR]."""
        for col, crit in criteria.items():
            if (
                (isinstance(crit, str) and crit == row[col])
                or (isinstance(crit, list) and row[col] in crit)
                or (isinstance(crit, t.Pattern) and crit.match(str(row[col])))
            ):
                return True

        return False

    for row in table:
        if include:
            if exclude and _match(exclude, row):
                continue
            if _match(include, row):
                yield row
        elif exclude and _match(exclude, row):
            continue
        else:
            yield row


@task
def print_table(
    *, table: list[RowData] | None = None, tables: Tables | None = None
) -> None:
    """Print a table."""
    if not tables:
        tables = {}
    if table:
        tables["_"] = table
    try:
        import pandas as pd
    except ImportError:
        pass
    else:
        # pd.set_option('display.max_rows', 1000)
        size = shutil.get_terminal_size()
        pd.set_option("display.width", size.columns)

        for tbl, nme in tables.items():
            dframe = pd.DataFrame(tbl)
            print(f"Table {nme}".strip())
            print(dframe)
        return

    for tbl, nme in tables.items():
        print(f"Table {nme} first 10 rows".strip())
        for row in tbl[:10]:
            print(" ", row)
        if len(tbl) > 10:
            print("  ...last 10:")
            for row in tbl[-10:]:
                print(" ", row)


@task
def remove_null(*, tables: abc.Sequence[list[RowData]]) -> None:
    """Remove nulls."""
    for table in tables:
        if not isinstance(table, list):
            _LOGGER.warning(
                "remove_null expected a list of tables, got %s %.100s",
                type(table),
                table,
            )

        for row in table:
            if not isinstance(row, dict):
                _LOGGER.warning(
                    "remove_null expected dict, got %s %.100s", type(row), row
                )
                continue
            for col in list(row.keys()):
                if row[col] is None:
                    del row[col]


@task
def replace(
    *, table: list[RowData], replace_dict: dict[str, str], columns: list[str]
) -> None:
    """Replace word in a column."""
    col = columns[0]
    for row in table:
        if col not in row:
            continue
        for _from, _to in replace_dict.items():
            if not _to:
                _to = _from + " "
            if row[col].find(_from) >= 0:
                row[col] = row[col].replace(_from, _to)


@task
def unique(*, table: list[RowData], key: str) -> RowDataGen:
    """Return rows with unique keys."""
    seen = {}
    for row in table:
        _key = row.get(key, None)
        if _key in seen:
            continue
        seen[_key] = True
        yield row


@task  # , tables=2, columns=3)
def vlookup(*, table0: list[RowData], acro: list[RowData], columns: list[str]) -> None:
    """Modify table0[col0], replacing table1[col1] with table1[col2]."""
    # _LOGGER.debug("Expand opt %s: len(acro)=%s", str(opt), len(acro))
    _acro: dict[str, t.Any] = {}
    for row in acro:
        key = str(row.get(columns[1], "")).lower()
        val = row.get(columns[2], "")
        if key in _acro:
            _LOGGER.debug("duplicate %s=%s (used: %s)", key, val, _acro[key])
            continue
        if key == "" or val == "":
            # _LOGGER.debug("bad key/val: key=%s  val=%s", key, val)
            continue
        _acro[key] = val
    _LOGGER.debug("Expand %s", str(_acro))

    for row0 in table0:
        val0 = str(row0.get(columns[0], "")).lower()
        if val0 in _acro:
            row0[columns[0]] = _acro[val0]
