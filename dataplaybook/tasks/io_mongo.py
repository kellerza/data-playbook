"""MongoDB IO tasks."""
import logging
from typing import List, Optional, Sequence
from urllib.parse import urlparse

import attr
import voluptuous as vol
from icecream import ic  # noqa pylint: disable=unused-import
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from dataplaybook import Columns, Table, task
from dataplaybook.utils import PlaybookError

_LOGGER = logging.getLogger(__name__)


def _clean_netloc(db_netloc: str) -> str:
    if "/" not in db_netloc:
        return db_netloc
    try:
        res = urlparse(db_netloc)
        return res.netloc
    except AttributeError as err:
        _LOGGER.error("could not parse URL: %s: %s", db_netloc, err)
        raise err


@attr.s(slots=True)
class MongoURI:
    """MongoDB URI."""

    netloc = attr.ib(converter=_clean_netloc)
    database = attr.ib()
    collection = attr.ib()
    set_id = attr.ib(default="")

    @staticmethod
    def new_from_string(db_uri: str, set_id=None):
        """Mongodb URI from a string."""
        try:
            res = urlparse(db_uri)
        except AttributeError as err:
            _LOGGER.error("could not parse URL: %s: %s", db_uri, err)
            raise err
        if res.scheme not in ["mdb", "mongodb", "db"]:
            raise vol.Invalid("mdb://host:port/database/collection/[set_id]")
        pth = res.path.split("/")

        if len(pth) == 4:
            if set_id:
                raise vol.InInvalid("set_id specified, not allowed in mdb URI")
            set_id = pth[3]

        return MongoURI(
            netloc=res.netloc,
            database=pth[1],
            collection=pth[2],
            set_id=set_id,
        )

    # @staticmethod
    # def validate(opt):
    #     """Validate MongoDB URI."""
    #     if not isinstance(opt.get("mdb"), MongoURI):
    #         opt["mdb"] = MongoURI.new_from_string(opt["mdb"], opt.pop("set_id", None))
    #     return opt

    def __str__(self) -> str:
        """As string."""
        return f"{self.netloc}/{self.database}/{self.collection}/{self.set_id}"

    def get_client(self, connect=True) -> MongoClient:
        """Return a MongoClient."""
        return MongoClient(self.netloc, connect=connect)


@task()
def read_mongo(
    mdb: MongoURI,
    *,
    set_id: Optional[str] = None,
) -> Table:
    """Read data from a MongoDB collection."""
    client = MongoClient(mdb.netloc, connect=True)
    if not set_id:
        set_id = mdb.set_id
    if set_id:
        cursor = client[mdb.database][mdb.collection].find({"_sid": set_id})
    else:
        cursor = client[mdb.database][mdb.collection].find()

    cursor.batch_size(200)
    for result in cursor:
        result.pop("_sid", None)
        result.pop("_id", None)
        yield result


@task()
def write_mongo(
    table: Table, mdb: MongoURI, *, set_id: Optional[str] = None, force=False
):
    """Write data to a MongoDB collection."""
    if not set_id:
        set_id = mdb.set_id
    try:
        client = MongoClient(mdb.netloc, connect=True)
        col = client[mdb.database][mdb.collection]
        if not set_id:
            _LOGGER.info("Writing %s documents", len(table))
            client[mdb.database][mdb.collection].insert_many(table)
            return

        filtr = {"_sid": set_id}
        existing_count = col.count_documents(filtr)
        if not force and existing_count > 0 and not table:
            _LOGGER.error(
                "Trying to replace %s documents with an empty set", existing_count
            )
            return
        _LOGGER.info(
            "Replacing %s documents matching %s, %s new",
            existing_count,
            set_id,
            len(table),
        )
        col.delete_many(filtr)
        if table:
            col.insert_many([dict(d, _sid=set_id) for d in table])
    except ServerSelectionTimeoutError as err:
        raise PlaybookError(f"Could not open connection to mdb {mdb}") from err


@task
def columns_to_list(table: Table, *, list_column: str, columns: Columns) -> None:
    """Convert columns with booleans to a list in a single column.

    Useful to store columns with true/false in a single list with the columns
    names.
    """
    for row in table:
        row[list_column] = [n for n in columns if row.pop(n, False)]


@task
def list_to_columns(table: Table, *, list_column: str, columns: Columns) -> None:
    """Convert a list with values to columns with True."""
    for row in table:
        for col in columns:
            if col in row[list_column]:
                row[col] = True
        del row[list_column]


@task
def mongo_list_sids(mdb: MongoURI) -> List[str]:
    """Return a list of _sids."""
    client = MongoClient(mdb.netloc, connect=True)
    cursor = client[mdb.database][mdb.collection]
    # non = cursor.find_one({"_sid": {"$exists": False}})
    # print(non)
    other = cursor.distinct("_sid")
    # print(other)
    return other


@task
def mongo_delete_sids(*, mdb: MongoURI, sids: List[str]):
    """Delete a specific _sid."""
    client = MongoClient(mdb.netloc, connect=True)
    cursor = client[mdb.database][mdb.collection]
    for sid in sids:
        if sid == "None" or sid is None:
            cursor.delete_many({"_sid": {"$exists": False}})
        else:
            cursor.delete_many({"_sid": sid})


@task
def mongo_sync_sids(
    *,
    mdb_local: MongoURI,
    mdb_remote: MongoURI,
    ignore_remote: Sequence[str] = None,
    only_sync_sids: Sequence[str] = None,
):
    """Sync two MongoDB collections.

    Only sync _sid's where the count is different.
    Dont delete additional SIDs from th remote if in ignore_remote
    """
    agg = [{"$group": {"_id": "$_sid", "count": {"$sum": 1}}}]
    # get local
    l_db = mdb_local.get_client()[mdb_local.database][mdb_local.collection]
    lsc = {i["_id"]: i["count"] for i in l_db.aggregate(agg)}
    # get remote
    r_db = mdb_remote.get_client()[mdb_remote.database][mdb_remote.collection]
    rsc = {i["_id"]: i["count"] for i in r_db.aggregate(agg)}

    for sid, lval in lsc.items():
        rval = rsc.pop(sid, None)
        if rval != lval:
            if only_sync_sids and sid not in only_sync_sids:
                continue
            # counts are different!
            mdb_local.set_id = sid
            lcl = read_mongo(mdb=mdb_local)
            write_mongo(mdb=mdb_remote, table=lcl, set_id=sid)

    if only_sync_sids:
        _LOGGER.info("Will not remove extra remote _sids")
        return

    extra = list(set(rsc.keys()) - set(ignore_remote or []))
    ic(extra)
    if extra:
        mongo_delete_sids(mdb=mdb_remote, sids=extra)
