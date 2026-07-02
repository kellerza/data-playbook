"""Pretty table helper."""

import logging
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from textwrap import wrap
from typing import Any

from prettytable import PrettyTable

_LOG = logging.getLogger(__name__)


def ensure_str(v: Any) -> str:
    """Ensure a value is a string."""
    return "" if v is None else str(v)


def pretty_table[T](
    headers: list[str],
    data: list[list[T]],
    /,
    wrap_length: int = 80,
    to_str: Callable[[T], str] = ensure_str,
    calculated_cols: dict[str, Callable[[list[T]], str]] | None = None,
) -> PrettyTable:
    """Print a table."""
    for row_any in data:
        if len(row_any) > len(headers):
            headers.extend([f"Extra {i}" for i in range(len(headers), len(row_any))])

    table = PrettyTable()
    table.field_names = headers

    if calculated_cols:
        calculated_cols = dict(calculated_cols)  # copy
        for colname in list(calculated_cols):
            if colname not in headers:
                headers.append(colname)
            idx = headers.index(colname)
            calculated_cols[str(idx)] = calculated_cols.pop(colname)

    for row_any in data:
        row = [to_str(v) for v in row_any]
        if calculated_cols:
            for colidx, func in calculated_cols.items():
                row[int(colidx)] = func(row_any)
        if wrap_length > 0:
            row = ["\n".join(wrap(v, wrap_length)) for v in row]
        table.add_row(row)

    return table


def table_data[T](
    data: Iterable[dict[str, T]], /, headers: list[str] | None = None
) -> tuple[list[str], list[list[T | None]]]:
    """Convert a list of dictionaries to a table data format."""
    if headers is None:
        headers = list({k for v in data for k in v.keys()})
    return headers, [[v.get(k) for k in headers] for v in data]


@dataclass(slots=True)
class StatSummary:
    """Accumulate labelled rows + stat counts for :func:`pretty_table`."""

    stat_cols: tuple[str, ...]
    label_cols: tuple[str, ...] = field(default_factory=tuple)
    detail_stats: tuple[str, ...] = field(default_factory=tuple)
    detail_col: str = "detail"
    rows: list[dict[str, str | int]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize column specs to ``frozenset`` for membership checks."""
        if "detail" in self.label_cols:
            self._warn("StatSummary labels include a reserved 'detail'.")

    @classmethod
    def stats(cls, /, **counts: int) -> dict[str, int]:
        """Step counts for :meth:`add`; omit zero values."""
        return {k: v for k, v in counts.items() if v}

    def _warn(self, msg: str) -> None:
        _LOG.warning(msg)
        self.warnings.append(msg)

    def _log_unknown(self, stats: dict[str, int], labels: dict[str, str | int]) -> None:
        if self.label_cols:
            if unknown := set(labels) - set(self.label_cols):
                self._warn(f"StatSummary unknown labels: {sorted(unknown)}")
            if missing := set(self.label_cols) - set(labels):
                self._warn(f"StatSummary missing labels: {sorted(missing)}")
        known = set(self.stat_cols) | set(self.detail_stats)
        if known and (unknown := set(stats) - known):
            self._warn(
                f"StatSummary unknown stats (→{self.detail_col}): {sorted(unknown)}"
            )

    def add(
        self,
        stats: dict[str, int],
        /,
        *,
        detail: str = "",
        **labels: str | int,
    ) -> None:
        """Append a row; ``stats`` keys in ``stat_cols`` become columns, rest go to ``detail``."""
        self._log_unknown(stats, labels)
        row = (
            {k: v for k, v in labels.items() if k in self.label_cols}
            if self.label_cols
            else dict(labels)
        )
        row.update({k: v for k, v in stats.items() if k in self.stat_cols})
        extras = " ".join(
            f"{k}={v}" for k, v in stats.items() if k not in self.stat_cols
        )
        parts = [p for p in (detail, extras) if p]
        if parts:
            row[self.detail_col] = " ".join(parts)
        self.rows.append(row)

    def print(
        self,
        *,
        wrap_length: int = 80,
        header: str = "",
    ) -> None:
        """Print the accumulated rows as a table, then any validation warnings."""
        table = str(pretty_table(*table_data(self.rows), wrap_length=wrap_length))
        text = f"{header}\n{table}" if header else table
        print(text, file=sys.stderr, flush=True)
        for msg in self.warnings:
            print(msg, file=sys.stderr, flush=True)
