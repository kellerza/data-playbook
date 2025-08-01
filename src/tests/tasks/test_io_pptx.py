"""Pptx tests."""

from pptx.dml.color import RGBColor

from dataplaybook.tasks.io_pptx import PStyle, Pt, PText


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
    assert t._list == ["a", PStyle(color=RGBColor(10, 11, 12))]

    t = PText("a", "<RED>")
    assert t._list == ["a", PStyle(color=RGBColor(255, 0, 0))]

    t = PText("a", "<RED,WHITE>")
    assert t._list == [
        "a",
        PStyle(color=(255, 0, 0), highlight=RGBColor(255, 255, 255)),
    ]

    t = PText("a", "<RED,WHITE>")
    assert t._list == [
        "a",
        PStyle(color=(255, 0, 0), highlight=RGBColor(255, 255, 255)),
    ]

    t = PText("a", "<,RED>")
    assert t._list == ["a", PStyle(highlight=RGBColor(255, 0, 0))]

    t = PText("a", PStyle(bold=True))
    t = PText("1", t)
    assert t._list == ["1", "a", PStyle(bold=True)]

    t = PText(" ", "zzz")
    assert t._list == [" ", "zzz"]

    t = PText(" ", PStyle(bold=True, italic=True, size=1), "zzz")
    assert t._list == [" ", PStyle(bold=True, italic=True, size=Pt(1)), "zzz"]


def test_ptext_newline() -> None:
    """Paragraph newline."""
    t = PText("abc\ndef")
    assert t._list == ["abc", "\n", "def"]

    t = PText("<8>\ndef")
    assert t._list == [PStyle(size=8), "\n", "def"]


def test_pstyle_size_pt() -> None:
    """Paragraph style size."""
    t = PText("<8>")
    assert t._list == [PStyle(size=Pt(8))]
    assert PStyle(size=Pt(8)) == PStyle(size=8)
    assert PStyle(size=Pt(1.1)) == PStyle(size=1.1)  # type:ignore[]


# def test_pstyle():

#     t = PStyle()
#     assert bool(t) is False

#     t = PStyle(bool=True)
#     assert bool(t)
