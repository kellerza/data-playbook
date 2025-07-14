"""DataPlayook init class."""

from os import PathLike

from dataplaybook.const import (
    DataEnvironment,
    RowData,
    RowDataGen,
    Tables,
)
from dataplaybook.main import _ENV as ENV
from dataplaybook.main import playbook, task

PathStr = PathLike | str

__all__ = [  # noqa:RUF022
    "DataEnvironment",
    "ENV",
    "playbook",
    "RowData",
    "RowDataGen",
    "Tables",
    "task",
]
