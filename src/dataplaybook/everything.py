r"""Search for files using Everything from voidtools.

Everything HTTP Example:
    http://localhost:8881/?s=zz%20xls&j=1&path_column=1
        { "totalResults":25, "results":[ { "type":"file",
        "name":"filename.xlsx", "path":"C:\\...." }
"""

import logging
from pathlib import Path

import attrs
import requests

_LOGGER = logging.getLogger(__name__)
SANE = r" !c:\windows !appdata\ !\.git !\.vscode !_old\ !.lnk !~$ !C:\program !c:\$R"
SERVER = "http://localhost:8881"


@attrs.define()
class Result:
    """Result of the search."""

    total: int
    files: list[Path] = attrs.field(factory=list)
    folders: list[Path] = attrs.field(factory=list)


def search(
    *terms: str,
    params: dict | None = None,
    sane: bool = True,
    sort: bool = True,
    max_results: int = 50,
) -> Result:
    """Search for files."""
    params = dict(
        {"s": " ".join(terms), "path_column": 1, "json": 1, "count": max_results},
        **(params or {}),
    )
    if sane:
        params["s"] += SANE
    if sort:
        params["sort"] = "date_modified"
        params["ascending"] = 0

    result = requests.get(SERVER, params=params, timeout=15)
    json = result.json()

    res = Result(total=json["totalResults"])
    for itm in json["results"]:
        if itm["type"] == "file":
            res.files.append(Path(itm["path"]) / itm.get("name", ""))
        elif itm["type"] == "folder":
            res.folders.append(Path(itm["path"]) / itm.get("name", ""))
        else:
            _LOGGER.error("Unknown type '%s' in result: %s", itm["type"], itm)
    return res
