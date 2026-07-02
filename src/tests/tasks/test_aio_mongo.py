"""Tests for async Motor equivalents of read_mongo/write_mongo."""

import pytest
from mongomock_motor import AsyncMongoMockClient
from motor.motor_asyncio import AsyncIOMotorCollection

from dataplaybook.tasks.aio_mongo import read_mongo_async, write_mongo_async


@pytest.fixture
async def mongo_col() -> AsyncIOMotorCollection:
    """In-memory Mongo collection for aio_mongo tests."""
    client: AsyncMongoMockClient = AsyncMongoMockClient()
    return client["testdb"]["testcol"]


# ---------------------------------------------------------------------------
# read_mongo_async
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_mongo_async_empty(mongo_col: AsyncIOMotorCollection) -> None:
    """Reading an empty collection yields nothing."""
    rows = [row async for row in read_mongo_async(col=mongo_col)]
    assert rows == []


@pytest.mark.asyncio
async def test_read_mongo_async_all(mongo_col: AsyncIOMotorCollection) -> None:
    """Without set_id, all documents are returned and _id/_sid stripped."""
    await mongo_col.insert_many([{"a": 1}, {"a": 2}])
    rows = [row async for row in read_mongo_async(col=mongo_col)]
    assert rows == [{"a": 1}, {"a": 2}]


@pytest.mark.asyncio
async def test_read_mongo_async_set_id_filters(
    mongo_col: AsyncIOMotorCollection,
) -> None:
    """Only documents matching set_id are returned."""
    await mongo_col.insert_many(
        [
            {"a": 1, "_sid": "s1"},
            {"a": 2, "_sid": "s2"},
            {"a": 3, "_sid": "s1"},
        ]
    )
    rows = [row async for row in read_mongo_async(col=mongo_col, set_id="s1")]
    assert rows == [{"a": 1}, {"a": 3}]


@pytest.mark.asyncio
async def test_read_mongo_async_strips_sid(mongo_col: AsyncIOMotorCollection) -> None:
    """_sid field is stripped from returned documents."""
    await mongo_col.insert_one({"a": 99, "_sid": "x"})
    rows = [row async for row in read_mongo_async(col=mongo_col, set_id="x")]
    assert rows == [{"a": 99}]
    assert "_sid" not in rows[0]


# ---------------------------------------------------------------------------
# write_mongo_async
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_mongo_async_no_set_id(mongo_col: AsyncIOMotorCollection) -> None:
    """Without set_id, documents are inserted as-is."""
    await write_mongo_async(col=mongo_col, table=[{"x": 1}, {"x": 2}])
    docs = await mongo_col.find({}, {"_id": 0}).to_list(None)
    assert docs == [{"x": 1}, {"x": 2}]


@pytest.mark.asyncio
async def test_write_mongo_async_with_set_id(mongo_col: AsyncIOMotorCollection) -> None:
    """With set_id, documents are stored with _sid attached."""
    await write_mongo_async(col=mongo_col, table=[{"x": 10}], set_id="s1")
    docs = await mongo_col.find({"_sid": "s1"}, {"_id": 0}).to_list(None)
    assert docs == [{"x": 10, "_sid": "s1"}]


@pytest.mark.asyncio
async def test_write_mongo_async_replaces_existing(
    mongo_col: AsyncIOMotorCollection,
) -> None:
    """Writing with an existing set_id replaces previous documents."""
    await write_mongo_async(col=mongo_col, table=[{"x": 1}], set_id="s1")
    await write_mongo_async(col=mongo_col, table=[{"x": 2}, {"x": 3}], set_id="s1")
    docs = await mongo_col.find({"_sid": "s1"}, {"_id": 0, "_sid": 0}).to_list(None)
    assert docs == [{"x": 2}, {"x": 3}]


@pytest.mark.asyncio
async def test_write_mongo_async_empty_table_with_existing_blocks(
    mongo_col: AsyncIOMotorCollection,
) -> None:
    """Writing an empty table over existing documents is blocked without force=True."""
    await write_mongo_async(col=mongo_col, table=[{"x": 1}], set_id="s1")
    await write_mongo_async(col=mongo_col, table=[], set_id="s1")
    count = await mongo_col.count_documents({"_sid": "s1"})
    assert count == 1


@pytest.mark.asyncio
async def test_write_mongo_async_force_allows_empty(
    mongo_col: AsyncIOMotorCollection,
) -> None:
    """force=True allows replacing existing documents with an empty table."""
    await write_mongo_async(col=mongo_col, table=[{"x": 1}], set_id="s1")
    await write_mongo_async(col=mongo_col, table=[], set_id="s1", force=True)
    count = await mongo_col.count_documents({"_sid": "s1"})
    assert count == 0


@pytest.mark.asyncio
async def test_write_mongo_async_multiple_set_ids_isolated(
    mongo_col: AsyncIOMotorCollection,
) -> None:
    """Documents from different set_ids are isolated during replacement."""
    await write_mongo_async(col=mongo_col, table=[{"x": 1}], set_id="s1")
    await write_mongo_async(col=mongo_col, table=[{"y": 2}], set_id="s2")
    await write_mongo_async(col=mongo_col, table=[{"x": 99}], set_id="s1")

    s1_docs = await mongo_col.find({"_sid": "s1"}, {"_id": 0, "_sid": 0}).to_list(None)
    s2_docs = await mongo_col.find({"_sid": "s2"}, {"_id": 0, "_sid": 0}).to_list(None)
    assert s1_docs == [{"x": 99}]
    assert s2_docs == [{"y": 2}]
