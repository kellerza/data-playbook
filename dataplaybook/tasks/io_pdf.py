"""PDF IO Tasks."""
import functools
import logging
import os
import subprocess
import tempfile
from pathlib import Path

import voluptuous as vol

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


def myreadlines(fobj, newline):
    """Readline with custom newline.

    https://stackoverflow.com/a/16260159
    """
    buf = ''
    for chunk in iter(functools.partial(fobj.read, 4096), ''):
        buf += chunk
        while newline in buf:
            pos = buf.index(newline)
            yield buf[:pos]
            buf = buf[pos + len(newline):]
    if buf:
        yield buf


@cv.task_schema({
    vol.Required('filename'): str
}, target=1)
def task_read_pdf_pages(tables, opt):
    """Read pdf as text pages."""
    if not opt.filename.lower().endswith('.pdf'):
        return
    try:
        _fd, to_name = tempfile.mkstemp()
        params = ['pdftotext', '-layout', opt.filename, to_name]
        _LOGGER.info("Converting %s", opt.filename)
        _LOGGER.debug("Calling with %s", params)
        subprocess.call(params)
        with open(to_name, 'r') as fle:
            for _no, text in enumerate(myreadlines(fle, chr(12)), 1):
                yield {'page': _no, 'text': text}
    finally:
        os.close(_fd)
        os.remove(to_name)


@cv.task_schema({
    vol.Required('folder'): str,
    vol.Optional('pattern', default='*.csv'): str
}, target=1)
def task_read_pdf_files(tables, opt):
    """Read all files in folder."""
    path = Path(opt.folder)
    files = sorted(path.glob(opt.pattern))
    _LOGGER.info("Open %s files", len(files))

    for filename in files:
        page_gen = task_read_pdf_pages({}, cv.AttrDict(
            {'filename': str(filename)}))
        for row in page_gen:
            row['filename'] = str(filename.name)
            yield row
