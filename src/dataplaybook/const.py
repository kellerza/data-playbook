"""Constants."""

from __future__ import annotations
from collections.abc import Generator
from typing import Any

from dataplaybook.helpers.env import DataEnvironment

type RowData = dict[str, Any]
RowDataGen = Generator[RowData, None, None]
Tables = dict[str, list[RowData]] | DataEnvironment

__all__ = (
    "DataEnvironment",
    "RowData",
    "RowDataGen",
    "Tables",
)
