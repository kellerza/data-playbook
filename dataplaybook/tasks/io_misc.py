"""Misc IO tasks."""
from json import dump, load
from os import getenv
from pathlib import Path
import time
from urllib.parse import urlparse
import urllib.request

import dataplaybook.config_validation as cv
import voluptuous as vol


@cv.task_schema(
    {vol.Required("patterns"): vol.All(cv.ensure_list, [str])}, target=True, kwargs=True
)
def task_glob(_, patterns):
    """Search for files matching certain patterns."""
    for val in patterns:
        fol, _, pat = val.partition("/*")
        folder = Path(fol)
        for file in folder.glob("*" + pat):
            yield {"file": str(file)}


@cv.task_schema(
    {vol.Required("file"): str, vol.Optional("count", default=3): int}, kwargs=True
)
def task_file_rotate(_, file, count):
    """Rotate some file fn.ext --> fn.1.ext --> fn.2.ext."""

    __f = Path(file)

    def _rename(start_fn, target_n):
        if not start_fn.exists():
            return
        target_fn = __f.with_suffix(f".{target_n}{__f.suffix}")
        if target_fn.exists():
            if target_n < count:
                _rename(target_fn, target_n + 1)
            else:
                target_fn.unlink()
                return
        start_fn.rename(target_fn)

    _rename(__f, 1)


@cv.task_schema(
    {
        vol.Required("file"): str,
        vol.Optional("columns"): vol.Any(None, vol.Schema({str: str})),
    },
    target=1,
    kwargs=True,
)
def task_read_csv(tables, file, columns=None):
    """Read csv file."""
    from csv import DictReader

    with open(file, "r", encoding="utf-8") as fle:
        csvf = DictReader(fle)
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


@cv.task_schema({vol.Required("file"): str}, target=(0, 1), kwargs=True)
def task_read_json(tables, file):
    """Read json from a file."""
    with Path(file).open("r", encoding="utf-8") as __f:
        res = load(__f)
        print(str(res)[:100])
        return res


@cv.task_schema(
    {vol.Required("file"): str, vol.Optional("only_var"): bool},
    tables=(0, 1),
    kwargs=True,
)
def task_write_json(tables, file, only_var=False):
    """Write into a json file."""
    with Path(file).open("w") as __f:
        dump(tables.var if only_var else tables, __f, indent="  ")


@cv.task_schema(
    {
        vol.Required("file"): str,
        vol.Optional("headers"): vol.All(cv.ensure_list, [cv.col_add]),
    },
    target=1,
)
def task_read_tab_delim(tables, opt):
    """Read xml file."""
    with open(opt.file, "r", encoding="utf-8") as fle:
        header = opt.headers if "headers" in opt else None
        for line in fle:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if header is None:
                header = line.split("\t")
                continue
            line = line.split("\t")
            yield {k: v for k, v in zip(header, line)}


@cv.task_schema(
    {
        vol.Required("filename"): str,
        vol.Required("newline"): object,
        vol.Optional("fields", default=None): object,
    },
    target=1,
    kwargs=True,
)
def task_read_text_regex(_, filename, newline, fields: None):
    """Much regular expressions into a table."""
    res = None
    with open(filename) as file:
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


@cv.task_schema(
    {
        vol.Required("file"): str,
        vol.Required("url"): str,
        vol.Optional("age", default=48 * 60 * 60): int,
    },
    kwargs=True,
)
def task_wget(tables, url, file, age):
    """Download a file."""
    path = Path(file)
    if path.exists():
        if time.time() - path.stat().st_mtime < age:
            return

    proxy = getenv("HTTP_PROXY")
    if proxy:
        dburl = urlparse(proxy)
        # create the object, assign it to a variable
        prx = "{}:{}".format(dburl.hostname, dburl.port)
        proxy = urllib.request.ProxyHandler({"http": prx, "https": prx, "ftp": prx})
        # construct a new opener using your proxy settings
        opener = urllib.request.build_opener(proxy)
        # install the openen on the module-level
        urllib.request.install_opener(opener)

    urllib.request.urlretrieve(url, file)


@cv.task_schema({vol.Required("file"): cv.endswith(".xlsx")}, tables=1, kwargs=True)
def task_write_csv(table, file):
    """Write a csv file."""
    from csv import DictWriter

    fieldnames = list(table[0].keys())

    with open(file, "w", newline="") as csvfile:
        writer = DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in table:
            writer.writerow(row)
