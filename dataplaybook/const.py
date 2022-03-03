"""Constants."""
from typing import Any, Dict, List, Union

from dataplaybook.utils import (  # noqa, pylint: disable=unused-import
    DataEnvironment,
    Table,
)

VERSION = "1.0.9"


Columns = List[str]
Column = str
# Defined in utils
# Table = List[Dict[str, Any]]
Tables = Union[Dict[str, List[Dict[str, Any]]], DataEnvironment]


class ATable(list):
    """A table/list with some metadata."""

    name: str = ""
    headers: int = 0
