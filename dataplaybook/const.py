"""Constants."""
from typing import Any, Union

from dataplaybook.helpers import DataEnvironment  # noqa, pylint: disable=unused-import
from dataplaybook.utils import Table  # noqa, pylint: disable=unused-import

VERSION = "1.0.16"


Columns = list[str]
Column = str
# Defined in utils
# Table = list[dict[str, Any]]
Tables = Union[dict[str, list[dict[str, Any]]], DataEnvironment]


class ATable(list):
    """A table/list with some metadata."""

    name: str = ""
    headers: int = 0
