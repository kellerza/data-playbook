"""Init."""

from __future__ import annotations
from dataclasses import dataclass, field

from dataplaybook.utils.parser import BaseClass, pre_process


@dataclass
class MyTest1(BaseClass):
    """Test class."""

    a: int = 0
    b: str = "1"


def test_default():
    """Omit defaults."""
    t = MyTest1()
    assert t.asdict() == {}


@pre_process()
@dataclass
class MyTest2(BaseClass):
    """Test class."""

    a: int = 0
    children: list[MyTest2] = field(default_factory=list)


def test_recursive() -> None:
    """Test recursive."""
    # test unstructure
    t = MyTest2(a=5, children=[MyTest2(a=6)])

    assert t.asdict() == {"a": 5, "children": [{"a": 6}]}
