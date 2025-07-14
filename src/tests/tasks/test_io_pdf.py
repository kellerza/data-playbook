"""Test PDF functions."""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from dataplaybook.tasks import io_pdf


@patch("dataplaybook.tasks.io_pdf.call")
def test_read_pages(pcall: Mock, caplog: pytest.LogCaptureFixture) -> None:
    """Test read pages."""
    data = f"a{chr(12)}b"

    mock_file = mock_open(read_data=data)
    with patch.object(Path, "open", mock_file):
        # with patch("pathlib.Path.open", m, create=True):
        res = list(io_pdf.read_pdf_pages(file="blah.pdf", args=[]))
        pcall.assert_called()

        assert res == [
            {"page": 1, "text": "a"},
            {"page": 2, "text": "b"},
        ]

        mock_file.side_effect = FileNotFoundError
        assert "Could not find pdftotext" not in caplog.text
        res = list(io_pdf.read_pdf_pages(file="blah.pdf", args=[]))
        assert "Could not find pdftotext" in caplog.text
        assert res == []
