"""Import all."""

import dataplaybook.tasks.all
import dataplaybook.tasks.fnb


def test_all() -> None:
    """Test all tasks import."""
    assert len(dir(dataplaybook.tasks.all)) > 10
    assert len(dir(dataplaybook.tasks.fnb)) > 2
