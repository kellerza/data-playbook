"""Fast JSON helpers using orjson."""

from datetime import datetime
from os import PathLike
from pathlib import Path, PurePath
from typing import Any, Literal

import orjson
from anyio import Path as AsyncPath
from whenever import Instant

from dataplaybook.utils.ensure import ensure_instant
from dataplaybook.utils.parser.convert import CONVERT

PathStr = PathLike | str


def orjson_dumpb(data: Any, *, indent: Literal[0, 2] = 0) -> bytes:
    """Dump the object."""
    opt = orjson.OPT_PASSTHROUGH_DATETIME + orjson.OPT_PASSTHROUGH_DATACLASS
    if indent:
        opt += orjson.OPT_INDENT_2
    return orjson.dumps(data, default=_default, option=opt)


def orjson_dumps(data: Any, indent: Literal[0, 2] = 0) -> str:
    """Dump as string."""
    return orjson_dumpb(data, indent=indent).decode(errors="replace")


def _default(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, PurePath):
        return str(obj)
    if isinstance(obj, datetime):
        return ensure_instant(obj).format_iso()  # type: ignore[union-attr]
    if isinstance(obj, Instant):
        return obj.format_iso()
    try:
        from bson import ObjectId, json_util
    except ImportError:
        json_util = None  # type: ignore[assignment,misc]
    else:
        if isinstance(obj, ObjectId):
            return json_util._encode_objectid(obj, None)
    try:
        return CONVERT.unstructure(obj)
    except TypeError:
        if json_util is not None:
            return json_util.default(obj)
        raise


def write_orjson(*, data: Any, file: PathStr, indent: Literal[0, 2]) -> None:
    """Write into a json file."""
    Path(file).write_bytes(orjson_dumpb(data, indent=indent))


async def orjson_aload(file: PathStr) -> Any:
    """Load from a json file."""
    asp = AsyncPath(file)
    if not await asp.exists():
        raise FileNotFoundError(f"File not found: {file}")
    return orjson.loads(await asp.read_bytes())


def orjson_load(file: PathStr) -> Any:
    """Load from a json file."""
    path = Path(file)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file}")
    return orjson.loads(path.read_bytes())
