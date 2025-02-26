"""Constants."""

from __future__ import annotations
from collections import abc
from typing import Any, TypeAlias

# pylint: disable=unused-import
from dataplaybook.helpers.env import DataEnvironment  # noqa: F401

RowData: TypeAlias = dict[str, Any]
RowDataGen: TypeAlias = abc.Generator[RowData, None, None]
Tables = dict[str, list[RowData]] | DataEnvironment
