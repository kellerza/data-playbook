"""MongoDB IO tasks."""
import logging

import voluptuous as vol
from pymongo import MongoClient

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


@cv.task_schema({
    vol.Required('database'): str,
    vol.Required('collection'): str,
    # table_id used in a MongoDB filter
    vol.Optional('table_id', default=None): vol.Any(str, None),
    vol.Optional('host', default='localhost:27017'): str,
}, target=1, kwargs=True)
def task_read_mongo(_, database, collection, table_id=None, host=None):
    """Read data from a MongoDB collection."""
    client = MongoClient(host, connect=True)
    if table_id:
        cursor = client[database][collection].find({'table_id': table_id})
    else:
        cursor = client[database][collection].find()

    cursor.batch_size(200)
    for result in cursor:
        result.pop('table_id', None)
        result.pop('_id', None)
        yield result


@cv.task_schema({
    vol.Required('database'): str,
    vol.Required('collection'): str,
    # table_id used in a MongoDB filter
    vol.Optional('table_id', default=None): vol.Any(str, None),
    vol.Optional('host', default='localhost:27017'): str,
}, tables=1, kwargs=True)
def task_write_mongo(table, database, collection, table_id=None, host=None):
    """Write data from a MongoDB collection."""
    client = MongoClient(host, connect=True)
    col = client[database][collection]
    if table_id:
        filtr = {'table_id': table_id}
        _LOGGER.debug("Replacing %s documents matching %s",
                      col.count(filtr), table_id)
        col.delete_many(filtr)
    _LOGGER.debug("Writing %s documents", len(table))

    client[database][collection].insert_many(
        [dict(d, table_id=table_id) for d in table])


# Useful to store columns with true/false in a list in Mongo documents.
@cv.task_schema({
    vol.Required('list'): str,
}, tables=1, columns=(1, 10))
def task_columns_to_list(table, opt):
    """Convert columns with bools to a list in a single column."""
    for row in table:
        row[opt.list] = [n for n in opt.columns if row.pop(n, False)]


@cv.task_schema({
    vol.Required('list'): str,
}, tables=1, columns=(1, 10))
def task_list_to_columns(table, opt):
    """Convert a list with values to columns wth True."""
    for row in table:
        for col in opt.columns:
            if col in row[opt.list]:
                row[col] = True
        del row[opt.list]
