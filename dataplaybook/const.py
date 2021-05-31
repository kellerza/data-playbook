"""Constants."""
from typing import Dict, List, Any, Union

from dataplaybook.utils import DataEnvironment

VERSION = "1.0.1"


Table = List[Dict[str, Any]]
Columns = List[str]
Column = str
Tables = Union[Dict[str, List[Dict[str, Any]]], DataEnvironment]


class ATable(list):
    """A table/list with some metadata."""

    name: str = ""
    headers: int = 0
