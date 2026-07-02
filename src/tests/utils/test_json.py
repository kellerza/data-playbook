"""Test orjson helpers."""

import logging
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import bson
import pytest
from whenever import Instant

from dataplaybook.utils.json import (
    orjson_aload,
    orjson_dumpb,
    orjson_dumps,
    orjson_load,
    write_orjson,
)
from dataplaybook.utils.parser import BaseClass

_LOG = logging.getLogger(__name__)


def test_dumps() -> None:
    """Dumps Instant and stdlib datetime."""
    dte = Instant.from_utc(2020, 1, 20)
    date_s = dte.format_iso()
    assert date_s == "2020-01-20T00:00:00Z"

    tests = [
        ({"date": dte.to_stdlib()}, '{"date":"2020-01-20T00:00:00Z"}'),
        ({"date": dte}, '{"date":"2020-01-20T00:00:00Z"}'),
    ]

    for idx, (val, exp) in enumerate(tests):
        _LOG.info("%s: {%s}", idx, exp)
        res = orjson_dumps(val)
        assert res == exp


def test_dumps_objectid() -> None:
    uid = bson.ObjectId("5f5e7b3b7b7b7b7b7b7b7b7b")

    tests = [
        ({"id": uid}, '{"id":{"$oid":"5f5e7b3b7b7b7b7b7b7b7b7b"}}'),
    ]

    for idx, (val, exp) in enumerate(tests):
        _LOG.info("%s: {%s}", idx, exp)
        res = orjson_dumps(val)
        assert res == exp


@dataclass
class _Sample(BaseClass):
    name: str = "x"
    count: int = 0


def test_dumps_baseclass() -> None:
    itm = _Sample(name="y", count=1)
    assert orjson_dumps(itm) == '{"name":"y","count":1}'


def test_dumps_path() -> None:
    assert orjson_dumps({"p": PurePosixPath("/a/b")}) == '{"p":"/a/b"}'


def test_dumps_indent() -> None:
    tests = [
        ({"id": 1}, '{\n  "id": 1\n}'),
        ({"id": 1, "id2": 2}, '{\n  "id": 1,\n  "id2": 2\n}'),
    ]

    for idx, (val, exp) in enumerate(tests):
        _LOG.info("%s: {%s}", idx, exp)
        res = orjson_dumps(val, indent=2)
        assert res == exp
        assert orjson_dumps(val, indent=0) != res


def test_roundtrip_file(tmp_path: Path) -> None:
    data = {"n": 1, "t": Instant.from_utc(2020, 1, 20)}
    write_orjson(data=data, file=tmp_path / "x.json", indent=2)
    loaded = orjson_load(tmp_path / "x.json")
    assert loaded == {"n": 1, "t": "2020-01-20T00:00:00Z"}


@pytest.mark.asyncio
async def test_orjson_aload(tmp_path: Path) -> None:
    p = tmp_path / "x.json"
    p.write_bytes(orjson_dumpb({"ok": True}))
    assert await orjson_aload(p) == {"ok": True}


@pytest.mark.asyncio
async def test_orjson_aload_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        await orjson_aload(tmp_path / "nope.json")
