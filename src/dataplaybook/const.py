"""Constants."""

from __future__ import annotations
from collections import abc
from typing import Any

# pylint: disable=unused-import
from dataplaybook.helpers.env import DataEnvironment  # noqa: F401

RowData = dict[str, Any]
RowDataGen = abc.Generator[RowData, None, None]
Tables = dict[str, list[RowData]] | DataEnvironment
