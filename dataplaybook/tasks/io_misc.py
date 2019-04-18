"""Misc IO tasks."""
from pathlib import Path

import voluptuous as vol

import dataplaybook.config_validation as cv


@cv.task_schema({
    vol.Required('file'): str,
    vol.Optional('columns'): vol.Any(None, vol.Schema({
        str: str
    })),
}, target=1, kwargs=True)
def task_read_csv(tables, file, columns=None):
    """Read csv file."""
    from csv import DictReader

    with open(file, 'r', encoding="utf-8") as fle:
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


@cv.task_schema({
    vol.Required('file'): str,
    vol.Optional('headers'): vol.All(cv.ensure_list, [cv.col_add])
}, target=1)
def task_read_tab_delim(tables, opt):
    """Read xml file."""
    with open(opt.file, 'r', encoding="utf-8") as fle:
        header = opt.headers if 'headers' in opt else None
        for line in fle:
            if line.startswith('#'):
                continue
            if header is None:
                header = line.split('\t')
                continue
            line = line.split('\t')
            yield {k: v for k, v in zip(header, line)}


@cv.task_schema({
    vol.Required('filename'): str,
    vol.Required('newline'): object,
    vol.Required('fields'): object,
}, target=1, kwargs=True)
def task_read_text_regex(_, filename, newline, fields):
    """Much regular expressions into a table."""
    res = None
    with open(filename) as file:
        for line in file:
            match_obj = newline.search(line)
            if match_obj:
                if res:
                    yield res
                res = {}
                res[match_obj[1]] = match_obj[2]
            if not res:
                continue
            for match_obj in fields.finditer(line):
                res[match_obj[1]] = match_obj[2]
    if res:
        yield res


@cv.task_schema({
    vol.Required('file'): str,
    vol.Required('url'): str,
    vol.Optional('age', default=48*60*60): int
}, kwargs=True)
def task_wget(tables, url, file, age):
    """Download a file."""
    from os import getenv
    import time
    import urllib.request
    from urllib.parse import urlparse

    path = Path(file)
    if path.exists():
        if time.time() - path.stat().st_mtime < age:
            return

    proxy = getenv('HTTP_PROXY')
    if proxy:
        dburl = urlparse(proxy)
        # create the object, assign it to a variable
        prx = "{}:{}".format(dburl.hostname, dburl.port)
        proxy = urllib.request.ProxyHandler(
            {'http': prx, 'https': prx, 'ftp': prx})
        # construct a new opener using your proxy settings
        opener = urllib.request.build_opener(proxy)
        # install the openen on the module-level
        urllib.request.install_opener(opener)

    urllib.request.urlretrieve(url, file)


@cv.task_schema({
    vol.Required('file'): cv.endswith('.xlsx'),
}, tables=1, kwargs=True)
def task_write_csv(table, file):
    """Write a csv file."""
    from csv import DictWriter

    fieldnames = list(table[0].keys())

    with open(file, 'w', newline='') as csvfile:
        writer = DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in table:
            writer.writerow(row)
