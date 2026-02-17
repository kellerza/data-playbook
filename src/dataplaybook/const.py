"""Constants."""

from __future__ import annotations
from typing import Any

from dataplaybook.helpers.env import DataEnvironment

type RowData = dict[str, Any]
type Tables = dict[str, list[RowData]] | DataEnvironment

__all__ = (
    "DataEnvironment",
    "RowData",
    "Tables",
)
