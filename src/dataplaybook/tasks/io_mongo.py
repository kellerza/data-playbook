"""MongoDB IO tasks."""

from __future__ import annotations
import logging
from collections import abc
from collections.abc import Generator
from dataclasses import InitVar, dataclass, field
from urllib.parse import urlparse

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError
from typing_extensions import deprecated  # In Python 3.13 it moves to warnings

from dataplaybook import RowData, task
from dataplaybook.utils import PlaybookError

_LOG = logging.getLogger(__name__)


def _clean_netloc(db_netloc: str) -> str:
    if "/" not in db_netloc:
        return db_netloc
    try:
        res = urlparse(db_netloc)
        return res.netloc
    except AttributeError as err:
        _LOG.error("could not parse URL: %s: %s", db_netloc, err)
        raise err


@dataclass(slots=True)
class MongoURI:
    """MongoDB URI."""

    from_str: InitVar[str]

    netloc: str = field(init=False)
    database: str = ""
    collection: str = ""
    set_id: str = ""

    client: MongoClient = field(init=False, repr=False)

    def __post_init__(self, from_str: str) -> None:
        """Post init."""
        self.client = None  # type:ignore[assignment]

        if from_str == "":
            raise ValueError("MongoURI cannot be empty")

        if "/" not in from_str:
            from_str = "mdb://" + from_str

        try:
            res = urlparse(from_str)
            self.netloc = res.netloc
        except AttributeError as err:
            _LOG.error("could not parse URL: %s: %s", from_str, err)
            raise err
        if res.scheme not in ["mdb", "mongodb", "db"]:
            raise ValueError(
                "Invalid Schema: mdb://host:port/database/collection/[set_id]"
            )
        pth = res.path.split("/")

        def _set_maybe(attr: str, val: str) -> None:
            curval = getattr(self, attr)
            if not curval:
                setattr(self, attr, val)
            elif val and curval != val:
                _LOG.debug("ignore %s='%s' in path %s, use '%s'", attr, val, curval)

        if len(pth) > 1 and (v := pth[1]):
            _set_maybe("database", v)
        if len(pth) > 2 and (v := pth[2]):
            _set_maybe("collection", v)
        if len(pth) > 3 and (v := pth[3]):
            _set_maybe("set_id", v)

    @deprecated("Use MongoURI() directly")
    @staticmethod
    def new_from_string(db_uri: str, set_id: str = "") -> MongoURI:
        """Old."""
        return MongoURI(db_uri, set_id=set_id)

    @deprecated("Use MongoURI() directly")
    @staticmethod
    def from_string(db_uri: str, set_id: str = "") -> MongoURI:
        """Mongodb URI from a string."""
        return MongoURI(db_uri, set_id=set_id)

    def __str__(self) -> str:
        """As string."""
        return f"{self.netloc}/{self.database}/{self.collection}/{self.set_id}"

    def get_client(self, connect: bool = True) -> MongoClient:
        """Return a MongoClient."""
        if self.client is None:
            self.client = MongoClient(self.netloc, connect=connect)
        return self.client

    def get_database(self, connect: bool = True) -> Database:
        """Return the Database from the MongoClient."""
        return self.get_client(connect=connect)[self.database]

    def get_collection(self, connect: bool = True) -> Collection:
        """Return the Collection from the MongoClient."""
        return self.get_database(connect=connect)[self.collection]


@task
def read_mongo(
    *,
    mdb: MongoURI,
    set_id: str | None = None,
) -> Generator[RowData]:
    """Read data from a MongoDB collection."""
    if not set_id:
        set_id = mdb.set_id
    col = mdb.get_collection()
    args = [{"_sid": set_id}] if set_id else []
    cursor = col.find(*args)

    cursor.batch_size(200)
    for result in cursor:
        result.pop("_sid", None)
        result.pop("_id", None)
        yield result


@task
def write_mongo(
    *,
    table: list[RowData],
    mdb: MongoURI,
    set_id: str | None = None,
    force: bool = False,
) -> None:
    """Write data to a MongoDB collection."""
    if not set_id:
        set_id = mdb.set_id
    try:
        col = mdb.get_collection()
        if not set_id:
            _LOG.info("Writing %s documents", len(table))
            col.insert_many(table)
            return

        filtr = {"_sid": set_id}
        existing_count = col.count_documents(filtr)
        if not force and existing_count > 0 and not table:
            _LOG.error(
                "Trying to replace %s documents with an empty set", existing_count
            )
            return
        _LOG.info(
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
def columns_to_list(
    *, table: list[RowData], list_column: str, columns: list[str]
) -> None:
    """Convert columns with booleans to a list in a single column.

    Useful to store columns with true/false in a single list with the columns
    names.
    """
    for row in table:
        row[list_column] = [n for n in columns if row.pop(n, False)]


@task
def list_to_columns(
    *, table: list[RowData], list_column: str, columns: list[str]
) -> None:
    """Convert a list with values to columns with True."""
    for row in table:
        for col in columns:
            if col in row[list_column]:
                row[col] = True
        del row[list_column]


@task
def mongo_list_sids(*, mdb: MongoURI) -> list[str]:
    """Return a list of _sids."""
    col = mdb.get_collection()
    return col.distinct("_sid")


@task
def mongo_delete_sids(*, mdb: MongoURI, sids: list[str]) -> None:
    """Delete a specific _sid."""
    col = mdb.get_collection()
    for sid in sids:
        if sid == "None" or sid is None:
            col.delete_many({"_sid": None})
        else:
            col.delete_many({"_sid": sid})


@task
def mongo_sync_sids(
    *,
    mdb_local: MongoURI,
    mdb_remote: MongoURI,
    ignore_remote: abc.Sequence[str] | None = None,
    only_sync_sids: abc.Sequence[str] | None = None,
) -> None:
    """Sync two MongoDB collections.

    Only sync _sid's where the count is different.
    Dont delete additional SIDs from th remote if in ignore_remote
    """
    agg = [{"$group": {"_id": "$_sid", "count": {"$sum": 1}}}]
    # get local
    l_db = mdb_local.get_collection()
    lsc = {i["_id"]: i["count"] for i in l_db.aggregate(agg)}
    # get remote
    r_db = mdb_remote.get_collection()
    rsc = {i["_id"]: i["count"] for i in r_db.aggregate(agg)}

    for sid, lval in lsc.items():
        rval = rsc.pop(sid, None)
        if rval != lval:
            if only_sync_sids and sid not in only_sync_sids:
                continue
            # counts are different!
            mdb_local.set_id = sid
            lcl = list(read_mongo(mdb=mdb_local))
            write_mongo(mdb=mdb_remote, table=lcl, set_id=sid)

    if only_sync_sids:
        _LOG.info("Will not remove extra remote _sids")
        return

    extra = list(set(rsc.keys()) - set(ignore_remote or []))
    if extra:
        _LOG.info("Removing sids: %s", extra)
        mongo_delete_sids(mdb=mdb_remote, sids=extra)
