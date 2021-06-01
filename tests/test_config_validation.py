"""Config Validaiton Tests."""
from unittest.mock import MagicMock, patch


def test_template_runtime():
    """Test template runtime."""
    with patch("dataplaybook.config_validation.vol.All", MagicMock()):
        pass
        # a = cv.templateSchema([])
