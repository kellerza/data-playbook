"""Async Motor equivalents of dataplaybook's read_mongo/write_mongo tasks."""

from __future__ import annotations
import logging
from collections import abc
from collections.abc import AsyncGenerator
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

_LOG = logging.getLogger(__name__)

RowData = dict[str, Any]

_DEFAULT_READ_PROJECTION: dict[str, Any] = {"_id": 0, "_sid": 0}


async def read_mongo_async(
    *,
    col: AsyncIOMotorCollection,
    set_id: str = "",
    proj: dict[str, Any] | None = None,
) -> AsyncGenerator[RowData]:
    """Read data from a MongoDB collection asynchronously.

    ``proj`` is passed to ``find`` as the projection. The default omits ``_id``
    and ``_sid``. Pass ``{}`` to return all fields, or any MongoDB projection
    dict you need.
    """
    filtr: RowData = {"_sid": set_id} if set_id else {}
    eff_proj = _DEFAULT_READ_PROJECTION if proj is None else proj
    cursor = col.find(filtr, eff_proj if eff_proj else None)
    cursor.batch_size(200)
    async for result in cursor:
        yield dict(result)


async def mongo_list_sids_async(*, col: AsyncIOMotorCollection) -> list[Any]:
    """Return distinct ``_sid`` values in the collection (same as ``mongo_list_sids``)."""
    return await col.distinct("_sid")


async def write_mongo_async(
    *,
    col: AsyncIOMotorCollection,
    table: list[RowData],
    set_id: str = "",
    force: bool = False,
) -> None:
    """Write data to a MongoDB collection asynchronously."""
    if not set_id:
        _LOG.info("Writing %s documents", len(table))
        await col.insert_many(table)
        return

    filtr = {"_sid": set_id}
    existing_count = await col.count_documents(filtr)
    if not force and existing_count > 0 and not table:
        _LOG.error("Trying to replace %s documents with an empty set", existing_count)
        return
    _LOG.info(
        "Replacing %s documents matching %s, %s new",
        existing_count,
        set_id,
        len(table),
    )
    await col.delete_many(filtr)
    if table:
        await col.insert_many([dict(d, _sid=set_id) for d in table])


async def delete_sids_async(
    *,
    col: AsyncIOMotorCollection,
    sids: list[str],
) -> None:
    """Delete all documents matching any of the given _sid values."""
    for sid in sids:
        await col.delete_many({"_sid": None if sid == "None" else sid})


async def mongo_sync_sids_async(
    *,
    mdb_local: AsyncIOMotorCollection,
    mdb_remote: AsyncIOMotorCollection,
    ignore_remote: abc.Sequence[str] | None = None,
    only_sync_sids: abc.Sequence[str] | None = None,
) -> None:
    """Sync two MongoDB collections.

    Only sync _sid's where the count is different.
    Don't delete additional SIDs from the remote if in ignore_remote.
    """
    agg = [{"$group": {"_id": "$_sid", "count": {"$sum": 1}}}]

    lsc = {i["_id"]: i["count"] async for i in mdb_local.aggregate(agg)}
    rsc = {i["_id"]: i["count"] async for i in mdb_remote.aggregate(agg)}

    for sid, lval in lsc.items():
        rval = rsc.pop(sid, None)
        if rval != lval:
            if only_sync_sids and sid not in only_sync_sids:
                continue
            # counts are different - read local, write to remote
            lcl = [row async for row in read_mongo_async(col=mdb_local, set_id=sid)]
            await write_mongo_async(col=mdb_remote, table=lcl, set_id=sid)

    if only_sync_sids:
        _LOG.info("Will not remove extra remote _sids")
        return

    extra = list(set(rsc.keys()) - set(ignore_remote or []))
    if extra:
        _LOG.info("Removing sids: %s", extra)
        await delete_sids_async(col=mdb_remote, sids=extra)
