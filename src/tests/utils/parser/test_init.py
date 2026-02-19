"""Init."""

from dataclasses import dataclass

from dataplaybook.utils.parser import BaseClass


@dataclass
class MyTest1(BaseClass):
    """Test class."""

    a: int = 0
    b: str = "1"


def test_default():
    """Omit defaults."""
    t = MyTest1()
    assert t.asdict() == {}
