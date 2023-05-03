"""Everything tests."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from dataplaybook.everything import search


@patch("dataplaybook.everything.requests")
def test_q(mock_requests):
    """Test a query."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "totalResults": 2,
        "results": [
            {
                "type": "file",
                "name": "filename.xlsx",
                "path": "C:/",
            },
            {"type": "folder", "path": "C:/", "name": ""},
        ],
    }

    mock_requests.get.return_value = mock_resp

    res = search("f1")
    assert res.total == 2
    assert res.files == [Path("C:/filename.xlsx")]
    assert res.folders == [Path("C:/")]
