"""Test PDF functions."""
from unittest.mock import Mock, mock_open, patch

from dataplaybook.tasks import io_pdf


@patch("dataplaybook.tasks.io_pdf.call")
def test_read_pages(pcall: Mock, caplog):
    """Test read pages."""

    data = f"a{chr(12)}b"

    m = mock_open(read_data=data)
    with patch("builtins.open", m, create=True):
        res = list(io_pdf.read_pdf_pages(filename="blah.pdf", args=[]))
        pcall.assert_called()

        assert res == [
            {"page": 1, "text": "a"},
            {"page": 2, "text": "b"},
        ]

        m.side_effect = FileNotFoundError
        assert "Could not find pdftotext" not in caplog.text
        res = list(io_pdf.read_pdf_pages(filename="blah.pdf", args=[]))
        assert "Could not find pdftotext" in caplog.text
        assert res == []
