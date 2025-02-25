"""Constants."""

from __future__ import annotations
import typing

# pylint: disable=unused-import
from dataplaybook.helpers.env import DataEnvironment  # noqa: F401

RowData = dict[str, typing.Any]
RowDataGen = typing.Generator[RowData, None, None]
Tables = dict[str, list[RowData]] | DataEnvironment
