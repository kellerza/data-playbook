"""XLSX tests."""
from unittest.mock import MagicMock, patch

from dataplaybook import DataEnvironment
from dataplaybook.tasks.io_xlsx import read_excel, write_excel
from dataplaybook.utils import AttrDict

# from openpyxl.worksheet.worksheet import Worksheet


@patch("openpyxl.load_workbook")
def test_read_excel(mock_load_workbook):
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

    read_excel(
        tables=tables,
        file="test.xlsx",
        sheets=[
            {"name": "Sheet1", "target": "table1"},
            {
                "name": "Sheet2",
                "target": "table2",
                "columns": {"name": {"from": "Name"}, "age": {"from": "Age"}},
            },
        ],
    )

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
def test_write_excel(mock_workbook):
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
        header=["Header 1", "Header 2"],
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
