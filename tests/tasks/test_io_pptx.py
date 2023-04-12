"""Pptx tests."""
from dataplaybook.tasks.io_pptx import PStyle, PText


def test_ptext() -> None:
    """Paragraph text."""
    t = PText("a", " b")
    assert t._list == ["a", " b"]

    t = PText("a", "<B>")
    assert t._list == ["a", PStyle(bold=True)]

    t = PText("a", "<->")
    assert t._list == ["a", PStyle(strike=True)]

    t = PText("a", "<I>")
    assert t._list == ["a", PStyle(italic=True)]

    t = PText("a", "<10>")
    assert t._list == ["a", PStyle(size=10)]

    t = PText("a", "<#0A0B0C>")
    assert t._list == ["a", PStyle(color=(10, 11, 12))]

    t = PText("a", "<RED>")
    assert t._list == ["a", PStyle(color=(255, 0, 0))]

    t = PText("a", "<RED,WHITE>")
    assert t._list == [
        "a",
        PStyle(color=(255, 0, 0), highlight=(255, 255, 255)),
    ]

    t = PText("a", "<RED,WHITE>")
    assert t._list == [
        "a",
        PStyle(color=(255, 0, 0), highlight=(255, 255, 255)),
    ]

    t = PText("a", "<,RED>")
    assert t._list == ["a", PStyle(highlight=(255, 0, 0))]

    t = PText("a", PStyle(bold=True))
    t = PText(t)
    assert t._list == ["a", PStyle(bold=True)]

    t = PText(" ", "zzz")
    assert t._list == [" ", "zzz"]

    t = PText(" ", PStyle(bold=True, italic=True, size=1), "zzz")
    assert t._list == [" ", PStyle(bold=True, italic=True, size=1), "zzz"]


def test_ptext_newline() -> None:
    """Paragraph newline."""
    t = PText("abc\ndef")
    assert t._list == ["abc", "\n", "def"]

    t = PText("<8>\ndef")
    assert t._list == [PStyle(size=8), "\n", "def"]


# def test_pstyle():

#     t = PStyle()
#     assert bool(t) is False

#     t = PStyle(bool=True)
#     assert bool(t)
