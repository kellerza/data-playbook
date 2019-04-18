"""MongoDB IO tasks."""
import logging
from urllib.parse import urlparse
import attr

import voluptuous as vol
from pymongo import MongoClient

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class MongoURI():
    """MongoDB URI."""
    netloc = attr.ib()
    database = attr.ib()
    collection = attr.ib()
    set_id = attr.ib()

    @staticmethod
    def from_string(uri):
        """Validate mongodb uri.
        Additional set_id"""
        res = urlparse(uri)
        if res.scheme != 'db':
            raise vol.Invalid("db://host:port/database/collection/[set_id]")
        pth = res.path.split('/')
        return MongoURI(
            netloc=res.netloc, database=pth[1], collection=pth[2],
            set_id=pth[3] if len(pth) == 4 else None)

    @staticmethod
    def from_dict(opt, db_field='db'):
        """Validate MongoDB URI. Allow override"""
        if isinstance(opt.db, str):
            opt[db_field] = MongoURI.from_string(opt[db_field])
        if 'set_id' in opt:
            if opt[db_field].set_id:
                raise vol.InInvalid("set_id specified, not allowed in db URI")
            opt[db_field].set_id = opt['set_id']
            del opt['set_id']
        return opt


@cv.task_schema({
    vol.Required('db'): str,
    vol.Optional('set_id'): str,
}, MongoURI.from_dict, target=1, kwargs=True)
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
    vol.Required('db'): str,
    vol.Optional('set_id'): str,
}, MongoURI.from_dict, tables=1, kwargs=True)
def task_write_mongo(table, db):  # pylint: disable=invalid-name
    """Write data from a MongoDB collection."""
    client = MongoClient(db.netloc, connect=True)
    col = client[db.database][db.collection]
    if db.set_id:
        filtr = {'_sid': db.set_id}
        existing_count = col.count(filtr)
        if existing_count > 0 and not table:
            _LOGGER.error("Trying to replace {} documents with an empty set")
            return
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
