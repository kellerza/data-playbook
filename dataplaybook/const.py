"""Constants."""
from typing import Any, Union

from dataplaybook.utils import (  # noqa, pylint: disable=unused-import
    DataEnvironment,
    Table,
)

VERSION = "1.0.12"


Columns = list[str]
Column = str
# Defined in utils
# Table = list[dict[str, Any]]
Tables = Union[dict[str, list[dict[str, Any]]], DataEnvironment]


class ATable(list):
    """A table/list with some metadata."""

    name: str = ""
    headers: int = 0
