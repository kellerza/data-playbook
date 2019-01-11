"""General tasks."""
import logging
import voluptuous as vol

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


@cv.task_schema({
    vol.Required('key'): cv.col_use,
}, target=1, tables=1, columns=(1, 10), kwargs=True)
def task_build_lookup(table, key, columns):
    """Build lookup tables by removing common columns and a key."""
    lookup = {}
    all_cols = list(columns)
    all_cols.insert(0, key)
    _LOGGER.warning(all_cols)
    for row in table:
        if not lookup.get(row[key]):
            yield {c: row.get(c) for c in all_cols}
            lookup[row[key]] = True
        for col in columns:
            row.pop(col)


@cv.task_schema({
    vol.Required('key'): cv.col_use,
    vol.Optional('value', default=True): vol.Any(True, str)
}, target=1, tables=(1, 10), columns=(0, 10))
def task_combine(*tables, opt):
    """Combine multiple tables on key.

    key: unique identifier for the rows
    columns: additional columns to add from the first table with the row
    target: output
    """
    _res = {}
    copy_columns = list(opt.columns)
    copy_columns.insert(0, opt.key)
    for table, table_name in zip(tables, opt.tables):
        for row in table:
            key = row[opt.key]
            if key not in _res:
                _res[key] = {k: row.get(k, "") for k in copy_columns}
            else:
                pass  # add redundant info...
            _res[key][table_name] = \
                True if opt.value is True else row[opt.value]
    return list(_res.values())


@cv.task_schema({
    vol.Required('drop'): vol.All(cv.ensure_list, [cv.table_remove])
})
def task_drop(tables, opt):
    """Drop tables from the active set."""
    for tbl in opt.drop:
        del tables[tbl]


def _validate_extend(schema):
    """Additional validate schema for extend."""
    for table in schema.tables:
        cv.table_use(table)
    return schema


@cv.task_schema({}, _validate_extend, tables=(2, 10))
def task_extend(*tables, opt):
    """Extend a table with another table."""
    for tbl in tables[1:]:
        tables[0].extend(tbl)


@cv.task_schema({
    vol.Optional('include', default={}): vol.Schema({cv.slug: object}),
    vol.Optional('exclude', default={}): vol.Schema({cv.slug: object})
}, tables=1, target=1)
def task_filter(table, opt):
    """Filter rows from a table."""
    def _match(criteria, row):
        """Test if row matches criteria [OR]."""
        for col, crit in criteria.items():
            if crit == row[col] or \
               (isinstance(crit, list) and row[col] in crit) or \
               (hasattr(crit, 'match') and crit.match(str(row[col]))):
                return True

        return False

    if opt.include:
        for row in table:
            if _match(opt.exclude, row):
                continue
            if _match(opt.include, row):
                yield row
        return

    for row in table:
        if not _match(opt.exclude, row):
            yield row


def _validate_fuzzy(val):
    cv.col_add(val.target_column, val.tables[1])
    cv.col_use(val.columns[0], val.tables[0])
    cv.col_use(val.columns[1], val.tables[1])
    return val


@cv.task_schema({
    vol.Required('target_column'): cv.slug
}, _validate_fuzzy, tables=2, columns=2)
def task_fuzzy_match(table1, table2, opt):
    """Fuzzy matching.

    https://marcobonzanini.com/2015/02/25/fuzzy-string-matching-in-python/
    """
    from fuzzywuzzy import fuzz  # process

    t2_colname = opt.columns[1]
    t2_names = list(set([str(r[t2_colname])
                         for r in table2 if r.get(t2_colname)]))
    t2_namesl = list(map(str.lower, t2_names))

    # print("cols:", opt.columns[0], opt.columns[1])
    for row in table1:
        col1 = row.get(opt.columns[0])
        if not col1:
            continue
        col1 = str(col1).lower()
        # res = process.extractBests(
        #     col1, t2_names, limit=10, scorer=fuzz.ratio)
        # row[opt.target_column] = '' if not res else res[0][0]
        # row[opt.target_column + '#'] = 0 if not res else res[0][1]
        # row[opt.target_column + '_'] = str(res)

        res = []
        for col2l, col2 in zip(t2_namesl, t2_names):
            resf = fuzz.ratio(col1, col2l)
            if resf > 20:
                res.append((resf, col2))
        res.sort(key=lambda rec: rec[0], reverse=True)
        row[opt.target_column] = '' if not res else res[0][1]
        row[opt.target_column + '#'] = 0 if not res else res[0][0]
        row[opt.target_column + '_'] = str(res[:10])


@cv.task_schema({}, tables=(1, 10))
def task_print(*tables, opt):
    """Prit a table."""
    import shutil
    try:
        import pandas as pd
    except ImportError:
        pass
    else:
        # pd.set_option('display.max_rows', 1000)
        size = shutil.get_terminal_size()
        pd.set_option('display.width', size.columns)

        for tbl, nme in zip(tables, opt.tables):
            dframe = pd.DataFrame(tbl)
            print("TABLE {}".format(nme))
            print(dframe)
        return

    for tbl, nme in zip(tables, opt.tables):
        print("TABLE {} first 10 rows".format(nme))
        for row in tbl[:10]:
            print(' ', row)
        if len(tbl) > 10:
            print("  ...last 10:")
            for row in tbl[-10:]:
                print(' ', row)


@cv.task_schema({
    vol.Required('replace'): dict,
}, tables=1, columns=1)
def task_replace(table, opt):
    """Replace word in a column."""
    col = opt.columns[0]
    for row in table:
        if col not in row:
            continue
        for _from, _to in opt.replace.items():
            if not _to:
                _to = _from + " "
            if row[col].find(_from) >= 0:
                row[col] = row[col].replace(_from, _to)


@cv.task_schema({
    vol.Required('key'): cv.col_use
}, tables=1, kwargs=True)
def task_unique(table, key):
    """Unique based on a key."""
    seen = {}
    for row in table:
        _key = row.get(key, None)
        if _key in seen:
            continue
        seen[_key] = 1
        yield row


@cv.task_schema({}, tables=2, columns=3)
def task_vlookup(table0, acro, opt):
    """Modify table0[col0], replacing table1[col1] with table1[col2]."""
    _LOGGER.debug("Expand opt %s: len(acro)=%s", str(opt), len(acro))
    _acro = {}
    for row in acro:
        key = str(row.get(opt.columns[1], "")).lower()
        val = row.get(opt.columns[2], "")
        if key in _acro:
            _LOGGER.debug("duplicate %s=%s (used: %s)", key, val, _acro[key])
            continue
        if key == '' or val == '':
            # _LOGGER.debug("bad acro: key=%s  val=%s", key, val)
            continue
        _acro[key] = val
    _LOGGER.debug("Expand %s", str(_acro))

    for row0 in table0:
        val0 = str(row0.get(opt.columns[0], '')).lower()
        if val0 in _acro:
            row0[opt.columns[0]] = _acro[val0]
