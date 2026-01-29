"""XLSX tests."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch

import pytz  # type: ignore[import]
from whenever import Instant

from dataplaybook import DataEnvironment
from dataplaybook.tasks.io_xlsx import Column, Sheet, _fmt, read_excel, write_excel
from dataplaybook.utils import AttrDict


@patch("openpyxl.load_workbook")
def test_read_excel(mock_load_workbook: Mock) -> None:
    """Test reading from an Excel file."""
    mock_workbook = MagicMock()
    mock_load_workbook.return_value = mock_workbook

    mock_sheet1 = MagicMock(title="Sheet1")
    mock_sheet1.rows = [
        [AttrDict(value="Name"), AttrDict(value="Age")],
        [AttrDict(value="Alice"), AttrDict(value=30)],
        [AttrDict(value="Bob"), AttrDict(value=25)],
    ].__iter__()
    mock_sheet2 = MagicMock(title="Sheet2")
    mock_sheet2.rows = [
        [AttrDict(value="Name"), AttrDict(value="Age")],
        [AttrDict(value="Charlie"), AttrDict(value=35)],
    ].__iter__()
    mock_workbook.__getitem__ = lambda self, x: {
        "Sheet1": mock_sheet1,
        "Sheet2": mock_sheet2,
    }.get(x)

    tables = DataEnvironment()

    reads = read_excel(
        tables=tables,
        file="test.xlsx",
        sheets=[
            Sheet(name="table1", source="Sheet1"),
            Sheet(
                name="table2",
                source="Sheet2",
                columns=[
                    Column(name="name", source="Name"),
                    Column(name="age", source="Age"),
                ],
            ),
        ],
    )
    assert reads == ["table1", "table2"]

    expected_tables = {
        "table1": [
            {"Name": "Alice", "Age": 30},
            {"Name": "Bob", "Age": 25},
        ],
        "table2": [
            {"name": "Charlie", "age": 35},
        ],
        "var": {},
    }
    assert tables == expected_tables

    mock_load_workbook.assert_called_once_with(
        "test.xlsx", read_only=True, data_only=True
    )
    mock_workbook.active.__eq__.assert_not_called()


@patch("openpyxl.Workbook")
def test_write_excel(mock_workbook: Mock) -> None:
    """Test writing to an Excel file."""
    mock_wbk = MagicMock()
    mock_workbook.return_value = mock_wbk

    tables = {
        "table1": [
            {"Name": "Alice", "Age": 30},
            {"Name": "Bob", "Age": 25},
        ],
        "table2": [
            {"name": "Charlie", "age": 35},
        ],
    }

    mock_sheet1 = MagicMock(title="Sheet1")
    mock_wbk.create_sheet.return_value = mock_sheet1

    write_excel(
        tables=tables,
        file="test.xlsx",
        include=["table1", "table2"],
        sheets=[
            Sheet(
                name="sheet1",
                source="Sheet1",
                columns=[Column(name="Header 1"), Column(name="Header 2")],
            )
        ],
    )

    # mock_wbk.create_sheet.assert_has_calls(
    #     [
    #         unittest.mock.call("table1"),
    #         unittest.mock.call("table2"),
    #     ]
    # )
    # mock_sheet1.append.assert_has_calls(
    #     [
    #         unittest.mock.call(["Header 1", "Header 2"]),
    #         unittest.mock.call(["Name", "Age"]),
    #         unittest.mock.call(["Alice", 30]),
    #         unittest.mock.call(["Bob", 25]),
    #         unittest.mock.call(["name", "age"]),
    #         unittest.mock.call(["Charlie", 35]),
    #     ]
    # )

    mock_wbk.save.assert_called_once_with("test.xlsx")


def test_from_old_read() -> None:
    """Test conversion from old format."""
    res = Sheet.from_old(
        {
            "name": "features",
            "target": "x",
            "header": 1,
            "columns": {
                "ref": {"col": 1},
                "action": {"col": 6},
            },
        }
    )
    assert res == [
        Sheet(
            name="x",
            source="features",
            header=1,
            columns=[
                Column(name="ref", source=1),
                Column(name="action", source=6),
            ],
        )
    ]

    res = Sheet.from_old({"name": "categoriesmap", "target": "categoriesmap"})
    assert res == [
        Sheet(
            name="categoriesmap",
            source="categoriesmap",
        )
    ]

    res = Sheet.from_old(
        {"name": "links", "target": "links", "columns": {"group": {"from": "group"}}}
    )
    assert res == [
        Sheet(
            name="links",
            source="links",
            columns=[
                Column(name="group", source="group"),
            ],
        )
    ]


def test_from_old_write() -> None:
    """Test conversion from old format."""
    res = Sheet.from_old(
        {
            "sheet": "erl",
            "columns": [
                {"name": "erl_id", "width": 8.43},
                {"name": "priority", "width": 9},
            ],
        }
    )
    assert res == [
        Sheet(
            name="erl",
            columns=[
                Column(name="erl_id", width=8.43),
                Column(name="priority", width=9),
            ],
        )
    ]


def test_fmt() -> None:
    """Test formatting function."""
    assert _fmt("Hello") == "Hello"
    assert _fmt(123) == 123
    assert _fmt(45.67) == 45.67
    assert _fmt(None) is None
    assert _fmt(True) is True
    assert _fmt(False) is False

    # Date & times
    assert _fmt(datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)) == datetime(
        2024, 1, 1, 12, 0, 0
    )
    naive = datetime(2024, 1, 1, 12, 0, 0)
    dt = pytz.timezone("Africa/Johannesburg").localize(naive)
    assert _fmt(dt) == datetime(2024, 1, 1, 10, 0, 0)
    assert _fmt(Instant("2022-10-24 17:00:00Z")) == datetime(2022, 10, 24, 17, 0, 0)
