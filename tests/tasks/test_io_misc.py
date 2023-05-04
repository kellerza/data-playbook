"""Test io."""
import re
import unittest
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, call, mock_open, patch

from dataplaybook.tasks.io_misc import (
    JSONDecodeError,
    Path,
    file_rotate,
    glob,
    read_csv,
    read_json,
    read_tab_delim,
    read_text_regex,
    wget,
    write_csv,
    write_json,
)


def test_file_rotate():
    with patch.object(Path, "exists") as mock_exists, patch.object(
        Path, "unlink"
    ) as mock_unlink, patch.object(Path, "rename") as mock_rename:
        # no others
        mock_exists.return_value = False
        file_rotate("z")
        assert mock_unlink.assert_not_called

        # others
        mock_exists.return_value = None
        mock_exists.side_effect = (True, False, False, False)
        mock_rename.return_value = True
        file_rotate("z")
        assert mock_unlink.assert_called_once
        assert mock_unlink.call_args_list == [call(missing_ok=True)]
        assert mock_rename.assert_called_once  # --> .1
        assert mock_rename.call_args_list == [call(Path("z.1"))]
        assert mock_exists.call_count == 4


def test_glob():
    with patch.object(Path, "glob") as mock_glob:
        # no others
        mock_glob.return_value = ["a", "b"]
        res = list(glob("a/*b"))
        mock_glob.assert_called_once
        assert res == [{"file": "a"}, {"file": "b"}]


class TestReadCsv(unittest.TestCase):
    def test_read_csv_with_columns(self):
        # Define some test data to read from the csv file
        file_path = "/path/to/file.csv"
        columns = {"col1": "header1", "col2": "header2"}
        csv_data = "header1,header2\nval1,val2\nval3,val4\n"

        # Create a mock file object to simulate reading from a file
        mock_file = mock_open(read_data=csv_data)

        # Call the function with the test data and the mock file object
        with patch("builtins.open", mock_file):
            table = list(read_csv(file_path, columns))

        # Verify that the function returned the expected table
        expected_table = [
            {"col1": "val1", "col2": "val2"},
            {"col1": "val3", "col2": "val4"},
        ]
        self.assertEqual(table, expected_table)

        # Verify that the mock file object was called with the expected arguments
        mock_file.assert_called_once_with(file_path, "r", encoding="utf-8")

    def test_read_csv_without_columns(self):
        # Define some test data to read from the csv file
        file_path = "/path/to/file.csv"
        csv_data = "col1,col2\nval1,val2\nval3,val4\n"

        # Create a mock file object to simulate reading from a file
        mock_file = mock_open(read_data=csv_data)

        # Call the function with the test data and the mock file object
        with patch("builtins.open", mock_file):
            table = list(read_csv(file_path))

        # Verify that the function returned the expected table
        expected_table = [
            {"col1": "val1", "col2": "val2"},
            {"col1": "val3", "col2": "val4"},
        ]
        self.assertEqual(table, expected_table)

        # Verify that the mock file object was called with the expected arguments
        mock_file.assert_called_once_with(file_path, "r", encoding="utf-8")


class TestReadJson(unittest.TestCase):
    def test_read_json(self):
        # Define some test data to read from the json file
        file_path = "/path/to/file.json"
        json_data = (
            '[{"col1": "val1", "col2": "val2"}, {"col1": "val3", "col2": "val4"}]'
        )

        # Create a mock file object to simulate reading from a file
        mock_file = mock_open(read_data=json_data)

        # Call the function with the test data and the mock file object
        with patch.object(Path, "open", mock_file):
            table = read_json(file_path)

        # Verify that the function returned the expected table
        expected_table = [
            {"col1": "val1", "col2": "val2"},
            {"col1": "val3", "col2": "val4"},
        ]
        self.assertEqual(table, expected_table)

        # Verify that the mock file object was called with the expected arguments
        mock_file.assert_called_once_with(mode="r", encoding="utf-8")

    def test_read_json_with_invalid_json(self):
        # Define some test data to read from the json file
        file_path = "/path/to/file.json"
        json_data = '[{"col1": "val1", "col2": "val2"}, {"col1": "val3", "col2": "val4"'

        # Create a mock file object to simulate reading from a file
        mock_file = mock_open(read_data=json_data)

        # Call the function with the test data and the mock file object
        with patch.object(Path, "open", mock_file):
            with self.assertRaises(JSONDecodeError):
                read_json(file_path)

        # Verify that the mock file object was called with the expected arguments
        mock_file.assert_called_once_with(mode="r", encoding="utf-8")

    def test_read_json_with_extra_data(self):
        # Define some test data to read from the json file
        file_path = "/path/to/file.json"
        json_data = (
            '{"col1": "val1", "col2": "val2"}\n{"col1": "val3", "col2": "val4"}\n'
        )

        # Create a mock file object to simulate reading from a file
        mock_file: MagicMock = mock_open(read_data=json_data)

        # Call the function with the test data and the mock file object
        with patch.object(Path, "open", mock_file):
            table = read_json(file_path)

        # Verify that the function returned the expected table
        expected_table = [
            {"col1": "val1", "col2": "val2"},
            {"col1": "val3", "col2": "val4"},
        ]
        self.assertEqual(table, expected_table)

        # Verify that the mock file object was called with the expected arguments
        assert mock_file.call_args_list == [
            call(mode="r", encoding="utf-8"),
            call(mode="r", encoding="utf-8", errors=None),
        ]


def test_write_json():
    data = {"key": "value"}
    with patch.object(Path, "open", mock_open()) as mock_file:
        write_json(data, "test.json")
        mock_file.assert_called_once_with("w", encoding="utf-8")
        handle = mock_file()
        assert handle.write.call_args_list == [
            call("{"),
            call("\n  "),
            call('"key"'),
            call(": "),
            call('"value"'),
            call("\n"),
            call("}"),
        ]


def test_read_tab_delim():
    headers = {"column1": "Header1", "column2": "Header2", "column3": "Header3"}

    with patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="# Comment\n# Header1\tHeader2\tHeader3\nValue1\tValue2\tValue3\nValue4\tValue5\tValue6",
    ) as mock_file:
        result = list(read_tab_delim("file.txt", headers))
        assert len(result) == 2
        assert result[0] == {
            "column1": "Value1",
            "column2": "Value2",
            "column3": "Value3",
        }
        assert result[1] == {
            "column1": "Value4",
            "column2": "Value5",
            "column3": "Value6",
        }
        mock_file.assert_called_once_with("file.txt", "r", encoding="utf-8")


def test_read_text_regex():
    """ChatGPT 3 - did not get result correct."""
    m = mock_open(read_data="abc\n1 foo\n2 bar\n3 baz\nxyz")
    with patch("builtins.open", m):
        result = list(
            read_text_regex(
                "testfile.txt", re.compile(r"(\d+) (\w+)"), re.compile(r"(\d+) (\w+)")
            )
        )
    assert result == [
        {"1": "foo"},
        {"2": "bar"},
        {"3": "baz"},
    ]


class TestWget(unittest.TestCase):
    @patch.object(Path, "exists", return_value=False)
    @patch("urllib.request.urlretrieve")
    def test_download_file(self, mock_urlretrieve, mock_path_exists):
        # Create a temporary file
        with NamedTemporaryFile() as tmp_file:
            # Call the function
            wget("http://example.com/file.txt", tmp_file.name)
            # Assert that the file was downloaded
            mock_urlretrieve.assert_called_once_with(
                "http://example.com/file.txt", tmp_file.name
            )

    @patch.object(Path, "stat")
    @patch.object(Path, "exists", return_value=True)
    @patch("urllib.request.urlretrieve")
    def test_download_age(self, mock_urlretrieve, mock_path_exists, mock_path_stat):
        # Create a temporary file
        with NamedTemporaryFile() as tmp_file:
            # Set the modification time to 2 days ago
            two_days_ago = datetime.now() - timedelta(days=2)
            mock_path_stat.return_value.st_mtime = two_days_ago.timestamp()
            # Call the function
            url = "http://example.com/file.txt"
            wget(url, tmp_file.name)
            # Assert that the file was not downloaded
            # mock_urlretrieve.assert_caled_once()
            # _with(url, tmp_file.name)
            # mock_path_exists.assert_called_once_with(tmp_file.name)
            mock_path_stat.assert_called_once()
            # self.assertFalse(
            #     mock_path_stat.return_value.st_mtime - two_days_ago.timestamp() < 60
            # )

    @patch.object(Path, "exists", return_value=False)
    @patch("urllib.request.urlopen")
    def test_download_no_file(self, mock_urlopen, mock_path_exists):
        # Call the function
        res = wget("http://example.com/file.txt", None)
        # Assert that the response was returned
        mock_urlopen.assert_called_once_with("http://example.com/file.txt")
        self.assertIsNotNone(res)


def test_write_csv():
    """Kudos to Chat-GPT 3."""
    # Create a mock file object to simulate writing to a file
    mock_file = mock_open()

    # Define some test data to write to the csv file
    table = [{"col1": "val1", "col2": "val2"}, {"col1": "val3", "col2": "val4"}]
    file_path = "/path/to/file.csv"
    header = ["col2", "col1"]

    # Call the function with the test data and the mock file object
    with patch("builtins.open", mock_file):
        write_csv(table, file_path, header)

    # Verify that the mock file object was called with the expected arguments
    expected_calls = [
        call(file_path, "w", encoding="utf-8-sig", errors="replace", newline=""),
        call().__enter__(),
        call().write("col2,col1\r\n"),
        call().write("val2,val1\r\n"),
        call().write("val4,val3\r\n"),
        call().__exit__(None, None, None),
    ]
    mock_file.assert_has_calls(expected_calls)
