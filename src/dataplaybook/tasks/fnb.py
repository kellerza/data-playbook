"""Merge FNB statement."""

import csv
import logging
import re
import typing
from calendar import monthrange
from collections import abc
from datetime import datetime
from pathlib import Path

from dataplaybook import PathStr, RowData, RowDataGen, task

_LOGGER = logging.getLogger(__name__)

RE_CARD = re.compile(r"\d{6}\*\d{4}")
RE_DATE = re.compile(r"\D?(\d{1,2})[ -]([A-Za-z]{3})\w* ?(\d{4})?\D?")
RE_DATE2 = re.compile(r"(\d{4})[ -/](\d{2})[ -/](\d{2})")
MONTH_MAP = {
    # Afr
    "jan": 1,
    "feb": 2,
    "mrt": 3,
    "apr": 4,
    "mei": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "okt": 10,
    "nov": 11,
    "des": 12,
    # Eng
    "mar": 3,
    "maa": 3,
    "oct": 10,
    "dec": 12,
    "may": 5,
}
CHANGE_DAY = 7  # The day at which the months change for budget purposes


def _budget_date(date: datetime) -> datetime:
    """Get a budget month date from the actual date."""
    if isinstance(date, datetime):
        if date.day > 7:
            return datetime(date.year, date.month, 1)
        if date.month > 1:  # decrease by 1 month
            return datetime(date.year, date.month - 1, 1)
        return datetime(date.year - 1, 12, 1)  # decrease year & month

    raise TypeError(f"Invalid date {date}")


def _str_to_date(text: str, year_month: datetime | None = None) -> datetime:
    """Convert statement text date to date."""
    if text is None:
        raise ValueError("Could not parse date '{text}'")

    match = RE_DATE.match(text)

    if match is None:
        match = RE_DATE2.match(text)
        if match is None:
            raise ValueError("Could not parse date '{text}'")
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    (year, month, day) = (match.group(3), match.group(2).lower(), int(match.group(1)))

    month = MONTH_MAP.get(month, month)
    if isinstance(month, str):
        raise ValueError("Invalid text month: {month}")

    # If no year, add from year_month
    if year is None and year_month is not None:
        year = year_month.year
        if month == 1 and year_month.month == 12:
            year += 1
    if year is not None:
        year = int(year)

    day = min(day, monthrange(year or 1900, month)[1])

    return datetime(year or 1900, month, day)


class InvalidFile(Exception):
    """Invalid file."""


@task
def read_cheque_csv(*, file: PathStr) -> RowDataGen:
    """Read an FNB cheque csv file."""
    fields = [
        "type",
        "nr",
        "date",
        "desc1",
        "desc2",
        "desc3",
        "amount",
        "saldo",
        "koste",
    ]
    data = {}
    file = Path(file)
    with file.open(newline="", encoding="utf-8") as csvfile:
        csvreader = csv.DictReader(csvfile, fields)
        for row in csvreader:
            try:
                rowtype = int(row[fields[0]])
            except ValueError as err:
                raise InvalidFile(
                    "read_cheque not a cheque file [{file.name}]"
                ) from err

            if rowtype == 2:  # Account number
                data["account"] = row[fields[1]]

            if rowtype == 3:  # Account id & date (last row)
                try:
                    data["id"] = int(row[fields[1]])
                except (ValueError, TypeError):
                    continue
                data["date"] = _str_to_date(row[fields[2]])

            if rowtype != 5:  # Standard transactions
                continue

            try:
                number = int(row[fields[1]])
            except (ValueError, TypeError):
                continue

            tdate = _str_to_date(row["date"], data["date"])  # type: ignore[arg-type]
            if tdate is None:
                continue

            res0 = {
                "amount": float(row["amount"]),
                "date": tdate,
                "id": f"{data['account']:0>16s}.{data['id']:04d}.{number:04d}",
                "description": row["desc2"],
                "extras": row["desc1"],
            }

            if RE_CARD.match(row["desc3"]) is None:
                res0["description"] += " " + str(row["desc3"])  # type: ignore[operator]
            else:
                res0["extras"] += " " + str(row["desc3"])  # type: ignore[operator]

            if " kontant" in res0["extras"].lower():  # type: ignore[operator, union-attr]
                res0["extras"], res0["description"] = (
                    res0["description"],
                    res0["extras"],
                )
            if res0["description"] == "":
                res0["description"] = res0["extras"]
                res0["extras"] = ""
            yield res0


TX_IDS: dict[tuple, int] = {}


def _get_id(acc: str, month: int) -> str:
    """Return an ID."""
    if acc is None:
        acc = "0"
    TX_IDS[(acc, month)] = TX_IDS.get((acc, month), 0) + 1
    return f"{acc:0>16s}.{month:04d}.{TX_IDS[(acc, month)]:04d}"


def _clean(row: dict) -> dict:
    """Strip space in row description."""
    if isinstance(row["description"], str):
        row["description"] = " ".join(row["description"].split())
    elif isinstance(row["description"], int | float):
        row["description"] = "''" + str(row["description"])
    else:
        _LOGGER.info("type %s", str(type(row["description"])))

    if not row["description"] and "extras" in row:
        row["description"] = row.pop("extras")
        return _clean(row)

    return row


@task
def fnb_process(*, tables: dict[str, list[RowData]]) -> RowDataGen:
    """Add the budget month and ID."""
    for _, t_table in tables.items():
        for row in t_table:
            if not any(row.values()):
                continue
            try:
                row["month"] = _budget_date(row["date"])
            except TypeError:
                _LOGGER.warning("Skip row %s", row)
                continue

            if "from" in row and "to" in row:
                # Cash transaction
                row["id"] = _get_id("custom", row["month"].month)
                f_t = ("# " + str(row.pop("to", "")), "# " + str(row.pop("from", "")))
                (row["extras"], row["description"]) = f_t
                yield _clean(row)

                row = row.copy()  # noqa: PLW2901
                (row["description"], row["extras"]) = f_t
                row["amount"] = -(row["amount"] or 0)
                yield _clean(row)

            # Cheque transaction
            elif "id" in row:
                yield _clean(row)

            # credit card
            else:
                row["id"] = _get_id(row.pop("card", ""), row["month"].month)
                row["extras"] = row.pop("place", "")
                try:
                    row["amount"] = -float(str(row["amount"]).replace(",", ""))
                except ValueError as exc:
                    raise ValueError("Error in {}: {}".format(row["id"], exc)) from exc
                yield _clean(row)


T = typing.TypeVar("T")


def _count_it(
    gen: abc.Generator[T, None, None], retval: dict
) -> abc.Generator[T, None, None]:
    """Count items yielded."""
    retval["count"] = 0
    for val in gen:
        retval["count"] += 1
        yield val
    retval["total"] = retval.get("total", 0) + retval["count"]


@task
def fnb_read_folder(*, folder: str, pattern: str = "*.csv") -> RowDataGen:
    """Read all files in folder."""
    path = Path(folder)
    files = sorted(path.glob(pattern))
    _LOGGER.info("Open %s files", len(files))

    retval: dict[str, int] = {}
    for filename in files:
        try:
            try:
                yield from _count_it(read_cheque_csv(file=str(filename)), retval)
                _LOGGER.info("Loaded %s lines from %s", retval["count"], filename)
                continue
            except InvalidFile:
                pass

            _LOGGER.warning("Could not load %s", filename)
        except Exception as err:
            _LOGGER.error("Could not read %s", filename, exc_info=err)
    _LOGGER.info("Success with %s lines", retval.get("total", 0))
