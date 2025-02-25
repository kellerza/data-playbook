"""DataPlayook init class."""

from os import PathLike
import typing as t

# ruff: noqa
from dataplaybook.const import (
    RowDataGen,
    Tables,
    DataEnvironment,
    RowData,
)
from dataplaybook.main import _ENV as ENV
from dataplaybook.main import playbook, task

PathStr = PathLike | str
