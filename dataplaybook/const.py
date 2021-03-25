"""Constants."""
from typing import Dict, List, Any

VERSION = "1.0.1"


Table = List[Dict[str, Any]]
Columns = List[str]
Column = str
Tables = Dict[str, List[Dict[str, Any]]]


class ATable(list):
    """A table/list with some metadata."""

    name: str = ""
    headers: int = 0


class PlaybookError(Exception):
    """Playbook Exception. These typically have warnings and can be ignored."""
