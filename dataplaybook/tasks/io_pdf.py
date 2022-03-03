"""PDF IO Tasks."""
import functools
import logging
import os
import tempfile
from pathlib import Path
from subprocess import call

from dataplaybook import Table, task

_LOGGER = logging.getLogger(__name__)


def _myreadlines(fobj, newline):
    """Readline with custom newline.

    https://stackoverflow.com/a/16260159
    """
    buf = ""
    for chunk in iter(functools.partial(fobj.read, 4096), ""):
        buf += chunk
        while newline in buf:
            pos = buf.index(newline)
            yield buf[:pos]
            buf = buf[pos + len(newline) :]
    if buf:
        yield buf


@task
def read_pdf_pages(filename: str) -> Table:
    """Read pdf as text pages."""
    if not filename.lower().endswith(".pdf"):
        return
    try:
        _fd, to_name = tempfile.mkstemp()
        params = ["pdftotext", "-layout", filename, to_name]
        _LOGGER.info("Converting %s", filename)
        _LOGGER.debug("Calling with %s", params)
        call(params, shell=False)
        with open(to_name, "r", encoding="utf-8", errors="replace") as __f:
            for _no, text in enumerate(_myreadlines(__f, chr(12)), 1):
                yield {"page": _no, "text": text}
    except FileNotFoundError:
        _LOGGER.error(
            "Could not find pdftotext executable. "
            "Download from https://www.xpdfreader.com/download.html"
        )
    finally:
        os.close(_fd)
        os.remove(to_name)


@task
def read_pdf_files(folder: str, pattern: str = "*.pdf") -> Table:
    """Read all files in folder."""
    path = Path(folder)
    files = sorted(path.glob(pattern))
    _LOGGER.info("Open %s files", len(files))

    for filename in files:
        page_gen = read_pdf_pages(filename=str(filename))
        for row in page_gen:
            row["filename"] = str(filename.name)
            yield row
