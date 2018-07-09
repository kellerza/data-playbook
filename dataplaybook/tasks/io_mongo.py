"""MongoDB IO tasks."""
import logging
from collections import namedtuple
from urllib.parse import urlparse

import voluptuous as vol
from pymongo import MongoClient

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


def validate_uri(uri):
    """Validate mongodb uri.
    Additional set_id"""
    mongo_uri = namedtuple('mongoUri', 'netloc database collection set_id')
    res = urlparse(uri)
    if res.scheme != 'db':
        raise vol.Invalid("db://host:port/database/collection/[set_id]")
    pth = res.path.split('/')
    return mongo_uri(
        res.netloc, pth[1], pth[2], pth[3] if len(pth) == 4 else None)


@cv.task_schema({
    vol.Required('db'): validate_uri,
}, target=1, kwargs=True)
def task_read_mongo(_, db):  # pylint: disable=invalid-name
    """Read data from a MongoDB collection."""

    client = MongoClient(db.netloc, connect=True)
    if db.set_id:
        cursor = client[db.database][db.collection].find(
            {'_sid': db.set_id})
    else:
        cursor = client[db.database][db.collection].find()

    cursor.batch_size(200)
    for result in cursor:
        result.pop('_sid', None)
        result.pop('_id', None)
        yield result


@cv.task_schema({
    vol.Required('db'): validate_uri,
}, tables=1, kwargs=True)
def task_write_mongo(table, db):  # pylint: disable=invalid-name
    """Write data from a MongoDB collection."""
    client = MongoClient(db.netloc, connect=True)
    col = client[db.database][db.collection]
    if db.set_id:
        filtr = {'_sid': db.set_id}
        _LOGGER.info("Replacing %s documents matching %s, %s new",
                      col.count(filtr), db.set_id, len(table))
        col.delete_many(filtr)
        client[db.database][db.collection].insert_many(
            [dict(d, _sid=db.set_id) for d in table])
        return

    _LOGGER.info("Writing %s documents", len(table))
    client[db.database][db.collection].insert_many(table)


@cv.task_schema({
    vol.Required('list'): str,
}, tables=1, columns=(1, 10))
def task_columns_to_list(table, opt):
    """Convert columns with bools to a list in a single column.

    Useful to store columns with true/false in a single list with the columns
    names.
    """
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
