"""Misc IO tasks."""
import time
import urllib.request
from csv import DictReader, DictWriter
from json import dump, load, loads
from json.decoder import JSONDecodeError
from os import getenv
from pathlib import Path
from typing import List, Optional, Pattern, Sequence
from urllib.parse import urlparse

from icecream import ic

from dataplaybook import Columns, Table, task


@task
def glob(patterns: List[str]) -> Table:
    """Search for files matching certain patterns."""
    for val in patterns:
        fol, _, pat = val.partition("/*")
        folder = Path(fol)
        for file in folder.glob("*" + pat):
            yield {"file": str(file)}


@task
def file_rotate(file: str, count: int = 3):
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
def read_csv(file: str, columns: Optional[Columns] = None) -> Table:
    """Read csv file."""
    with open(file, "r", encoding="utf-8") as __f:
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
def read_json(file) -> Table:
    """Read json from a file."""
    try:
        with Path(file).open("r", encoding="utf-8") as __f:
            res = load(__f)
            print(str(res)[:100])
            return res
    except JSONDecodeError as err:
        if err.msg != "Extra data":
            raise
    # Extra data, so try load line by line
    res = []
    for line in Path(file).read_text(encoding="utf8").splitlines():
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
def write_json(tables, file: str, only_var=False) -> None:
    """Write into a json file."""
    with Path(file).open("w", encoding="utf8") as __f:
        dump(tables.var if only_var else tables, __f, indent="  ")


@task
def read_tab_delim(file, headers: Columns) -> Table:
    """Read xml file."""
    with open(file, "r", encoding="utf-8") as __f:
        header = headers
        for line in __f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if header is None:
                header = line.split("\t")
                continue
            line = line.split("\t")
            yield dict(zip(header, line))


@task
def read_text_regex(
    filename: str, newline: Pattern, fields: Optional[Pattern]
) -> Table:
    """Much regular expressions into a table."""
    res = None
    with open(filename, encoding="utf8") as file:
        for line in file:
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
                res[match_obj[1]] = match_obj[2]
    if res:
        yield res


@task
def wget(url: str, file: str, age: int = 48 * 60 * 60):
    """Download a file."""
    if file:
        path = Path(file)
        if path.exists():
            if time.time() - path.stat().st_mtime < age:
                return

    proxy = getenv("HTTP_PROXY")
    if proxy:
        dburl = urlparse(proxy)
        # create the object, assign it to a variable
        prx = f"{dburl.hostname}:{dburl.port}"
        proxy = urllib.request.ProxyHandler({"http": prx, "https": prx, "ftp": prx})
        # construct a new opener using your proxy settings
        opener = urllib.request.build_opener(proxy)
        # install the openen on the module-level
        urllib.request.install_opener(opener)

    if file:
        urllib.request.urlretrieve(url, file)
    else:
        return urllib.request.urlopen(url)


@task
def write_csv(table: Table, file: str, header: Sequence[str] = None) -> None:
    """Write a csv file."""
    fieldnames = list(table[0].keys())
    for hdr in reversed(header):
        if hdr in fieldnames:
            fieldnames.remove(hdr)
        fieldnames.insert(0, hdr)

    with open(file, "w", encoding="utf-8-sig", errors="replace", newline="") as csvfile:
        writer = DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in table:
            writer.writerow(row)
