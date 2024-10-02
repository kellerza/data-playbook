"""Constants."""

from __future__ import annotations
import typing

# pylint: disable=unused-import
from dataplaybook.helpers.env import DataEnvironment  # noqa: F401

VERSION = "1.0.20"

Columns = list[str]
Column = str
RowData = dict[str, typing.Any]
RowDataGen = typing.Generator[RowData, None, None]
Tables = dict[str, list[RowData]] | DataEnvironment


# @attrs.define(slots=True)
# class Result(list[dict[str, typing.Any]]):
#     """A table/list with some metadata."""

#     name: str = attrs.field(default="")
#     headers: int = 0
