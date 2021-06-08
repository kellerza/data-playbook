"""Tests for main tasks"""
import re

from dataplaybook import DataEnvironment
from dataplaybook.tasks import (
    build_lookup,
    build_lookup_var,
    ensure_lists,
    filter_rows,
    print_table,
    replace,
    unique,
    vlookup,
)


def _streets():
    return [
        dict(street="W", suburb="A", postcode=1001),
        dict(street="X", suburb="B", postcode=2002),
        dict(street="Y", suburb="B", postcode=2002),
        dict(street="Z", suburb="A", postcode=1001),
    ]


def test_task_build_lookup():
    """Test build_lookup."""
    tables = DataEnvironment()
    tables["streets"] = _streets()

    tables["area"] = build_lookup(
        table=tables["streets"], key="postcode", columns=["suburb"]
    )

    assert tables.area == [
        dict(postcode=1001, suburb="A"),
        dict(postcode=2002, suburb="B"),
    ]

    assert tables.streets == [
        dict(street="W", postcode=1001),
        dict(street="X", postcode=2002),
        dict(street="Y", postcode=2002),
        dict(street="Z", postcode=1001),
    ]


def test_task_build_lookup_var():
    """Test build_lookup_var."""
    tables = DataEnvironment()
    tables["streets"] = _streets()

    hse = build_lookup_var(
        table=tables["streets"], key="street", columns=["suburb", "postcode"]
    )
    assert hse["W"] == dict(suburb="A", postcode=1001)


def test_task_ensure_lists():
    """Test ensure_list."""
    tables = DataEnvironment()
    tables["streets"] = _streets()

    ensure_lists(tables=tables.as_list("streets"), columns=["suburb"])
    assert tables["streets"][0] == dict(street="W", suburb=["A"], postcode=1001)


def test_task_filter():
    """Test filter."""
    tables = DataEnvironment()
    tables["streets"] = _streets()
    # Include
    tables["X"] = filter_rows(table=tables.streets, include={"street": "X"})

    assert tables.X == [dict(street="X", suburb="B", postcode=2002)]

    # Include and exclude some
    tables["X2"] = filter_rows(
        table=tables.streets,
        include={"suburb": "B"},
        exclude={"street": "Y"},
    )
    assert tables.X2 == [dict(street="X", suburb="B", postcode=2002)]

    # Exclude
    tables["X3"] = filter_rows(
        table=tables.streets,
        exclude={"street": "X"},
    )
    assert len(tables.X3) == 3

    # List in terms...
    tables["X4"] = filter_rows(
        table=tables.streets,
        exclude={"street": ["Y", "W", "Z"]},
    )
    assert tables.X4 == [dict(street="X", suburb="B", postcode=2002)]

    # Regular expression in terms
    tables["X5"] = filter_rows(
        table=tables.streets,
        exclude={"street": re.compile("[YWZ]")},
    )
    assert tables.X5 == [dict(street="X", suburb="B", postcode=2002)]


def test_task_replace():
    """Test replace."""
    tables = DataEnvironment()
    tables["streets"] = _streets()

    replace(
        table=tables.streets, replace_dict={"A": "A_", "B": "B_"}, columns=["suburb"]
    )

    _ss = {s["suburb"] for s in tables.streets}
    assert _ss == set(["A_", "B_"])


def test_task_print():
    """Test print."""
    tables = DataEnvironment()
    tables["streets"] = _streets()
    tables["streets2"] = _streets()

    print_table(tables=tables.as_dict("streets", "streets2"))


def test_task_unique():
    """Test unique."""
    tables = DataEnvironment()
    tables["streets"] = _streets()

    tables["X"] = unique(table=tables.streets, key="suburb")

    assert tables.X == [
        dict(street="W", suburb="A", postcode=1001),
        dict(street="X", suburb="B", postcode=2002),
    ]


def test_task_vlookup():
    """Test vlookup."""
    tables = DataEnvironment()
    tables["streets"] = _streets()

    tables["area"] = build_lookup(
        table=tables.streets, key="postcode", columns=["suburb"]
    )

    vlookup(
        table0=tables.streets,
        acro=tables.area,
        columns=["postcode", "postcode", "suburb"],
    )

    assert tables.streets == [
        dict(postcode="A", street="W"),
        dict(postcode="B", street="X"),
        dict(postcode="B", street="Y"),
        dict(postcode="A", street="Z"),
    ]
