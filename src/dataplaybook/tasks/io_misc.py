"""Misc IO tasks."""

import re
import time
from csv import DictReader, DictWriter
from json import dump, load, loads
from json.decoder import JSONDecodeError
from os import getenv
from pathlib import Path
from typing import Any

import requests
from icecream import ic

from dataplaybook import (
    DataEnvironment,
    PathStr,
    RowData,
    RowDataGen,
    Tables,
    task,
)
from dataplaybook.utils import ensure_list as _ensure_list


@task
def file_rotate(*, file: PathStr, count: int = 3) -> None:
    """Rotate some file fn.ext --> fn.1.ext --> fn.2.ext."""
    f_n = Path(file)
    if not f_n.exists():
        return
    t_f = f_n.with_suffix(f".{count}{f_n.suffix}")
    # Remove last file
    t_f.unlink(missing_ok=True)
    for idx in range(count - 1, 0, -1):
        s_f = f_n.with_suffix(f".{idx}{f_n.suffix}")
        if s_f.exists():
            s_f.rename(t_f)
        t_f = s_f
    # Rename first file
    f_n.rename(t_f)


@task
def glob(*, patterns: list[str]) -> RowDataGen:
    """Search for files matching certain patterns."""
    for val in _ensure_list(patterns):  # type: ignore[]
        fol, _, pat = val.partition("/*")
        folder = Path(fol)
        for file in folder.glob("*" + pat):
            yield {"file": str(file)}


@task
def read_csv(*, file: PathStr, columns: dict[str, str] | None = None) -> RowDataGen:
    """Read csv file."""
    with Path(file).open("r", encoding="utf-8") as __f:
        csvf = DictReader(__f)
        # header = opt.headers if 'headers' in opt else None
        for line in csvf:
            if columns:
                yield {k: line.get(v) for k, v in columns.items()}
            else:
                yield line
            # if line.startswith('#'):
            #     continue
            # if header is None:
            #     header = line.split('\t')
            #     continue
            # line = line.split('\t')
            # yield {k: v for k, v in zip(header, line)}


@task
def read_json(*, file: PathStr) -> list[RowData]:
    """Read json from a file."""
    try:
        with Path(file).open(mode="r", encoding="utf-8") as __f:
            res = load(__f)
            print(str(res)[:100])
            return res
    except JSONDecodeError as err:
        if err.msg != "Extra data":
            raise
    # Extra data, so try load line by line
    res = []
    for line in Path(file).read_text(encoding="utf-8").splitlines():
        try:
            if line.strip() == "":
                continue
            res.append(loads(line))
        except Exception:
            ic(line)
            ic("exc2")
            raise
    return res


@task
def write_json(
    *, data: Tables | list[RowData], file: PathStr, only_var: bool = False
) -> None:
    """Write into a json file."""
    with Path(file).open("w", encoding="utf-8") as __f:
        if only_var:
            data = data.var if isinstance(data, DataEnvironment) else {}
        dump(data, __f, indent="  ")


@task
def read_tab_delim(*, file: PathStr, headers: list[str]) -> RowDataGen:
    """Read xml file."""
    with Path(file).open("r", encoding="utf-8") as __f:
        header = headers
        for line in __f:
            line = line.strip()  # noqa: PLW2901
            if line.startswith("#") or not line:
                continue
            if header is None:
                header = line.split("\t")
                continue
            vals = line.split("\t")
            yield dict(zip(header, vals, strict=False))


@task
def read_text_regex(
    *, file: PathStr, newline: re.Pattern, fields: re.Pattern | None
) -> RowDataGen:
    """Much regular expressions into a table."""
    res: dict[str, Any] | None = None
    with Path(file).open(encoding="utf-8") as fptr:
        for line in fptr:
            match_obj = newline.search(line)
            if match_obj:
                if res:
                    yield res
                res = {}
                groups = match_obj.groups()
                if len(groups) > 1:
                    res[groups[0]] = groups[1]
                elif len(groups) > 0:
                    res["_id_"] = groups[0]
            if res is None:
                continue
            if not fields:
                continue
            for match_obj in fields.finditer(line):
                res[match_obj[1]] = match_obj[2]  # type:ignore[]
    if res:
        yield res


@task
def wget(
    *,
    url: str,
    file: PathStr,
    age: int = 48 * 60 * 60,
    headers: dict[str, str] | None = None,
) -> None:
    """Get a file from the web."""
    path = Path(file)
    if file:
        if path.exists():
            if time.time() - path.stat().st_mtime < age:
                return

    proxies = {
        "http": getenv("HTTP_PROXY") or "",
        "https": getenv("HTTPS_PROXY") or getenv("HTTP_PROXY") or "",
        "ftp": getenv("FTP_PROXY") or getenv("HTTP_PROXY") or "",
    }
    proxies = {k: v for k, v in proxies.items() if v}
    headers = headers or {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    with requests.get(
        url, stream=True, proxies=proxies, headers=headers, timeout=15
    ) as r:
        r.raise_for_status()
        with path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)


@task
def write_csv(
    *, table: list[RowData], file: PathStr, header: list[str] | None = None
) -> None:
    """Write a csv file."""
    fieldnames = list(table[0].keys())
    for hdr in reversed(header or []):
        if hdr in fieldnames:
            fieldnames.remove(hdr)
        fieldnames.insert(0, hdr)

    with Path(file).open(
        "w", encoding="utf-8-sig", errors="replace", newline=""
    ) as csvfile:
        writer = DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in table:
            writer.writerow(row)
