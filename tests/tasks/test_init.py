"""Tests for main tasks"""
import re

import dataplaybook.config_validation as cv
from dataplaybook import DataPlaybook


def _table_add(dpb):
    for key in dpb.tables:
        if key != 'var':
            cv.table_add(key)


def _streets():
    return [
        dict(street='W', suburb='A', postcode=1001),
        dict(street='X', suburb='B', postcode=2002),
        dict(street='Y', suburb='B', postcode=2002),
        dict(street='Z', suburb='A', postcode=1001),
    ]


def test_task_build_lookup():
    """Test build_lookup."""
    dpb = DataPlaybook(modules='dataplaybook.tasks')
    dpb.tables['streets'] = _streets()
    _table_add(dpb)

    dpb.execute_task({
        'tables': 'streets', 'target': 'area',
        'build_lookup': {
            'key': 'postcode',
            'columns': ['suburb'],
        }})

    assert dpb.tables.area == [
        dict(postcode=1001, suburb='A'),
        dict(postcode=2002, suburb='B'),
    ]
    assert dpb.tables.streets == [
        dict(street='W', postcode=1001),
        dict(street='X', postcode=2002),
        dict(street='Y', postcode=2002),
        dict(street='Z', postcode=1001),
    ]


def test_task_build_lookup_var():
    """Test build_lookup_var."""
    from tests.tasks.test_templates import test_templateSchema_readme_example
    test_templateSchema_readme_example()


def test_task_filter():
    """Test filter."""
    dpb = DataPlaybook(modules='dataplaybook.tasks')
    dpb.tables['streets'] = _streets()
    _table_add(dpb)

    # Include
    dpb.execute_task({
        'tables': 'streets', 'target': 'X',
        'filter': {
            'include': {'street': 'X'},
        }})
    assert dpb.tables.X == [dict(street='X', suburb='B', postcode=2002)]

    # Inlude and exclude some
    dpb.execute_task({
        'tables': 'streets', 'target': 'X2',
        'filter': {
            'include': {'suburb': 'B'},
            'exclude': {'street': 'Y'},
        }})
    assert dpb.tables.X2 == [dict(street='X', suburb='B', postcode=2002)]

    # Exclude
    dpb.execute_task({
        'tables': 'streets', 'target': 'X3',
        'filter': {
            'exclude': {'street': 'X'},
        }})
    assert len(dpb.tables.X3) == 3

    # List in terms...
    dpb.execute_task({
        'tables': 'streets', 'target': 'X4',
        'filter': {
            'exclude': {'street': ['Y', 'W', 'Z']},
        }})
    assert dpb.tables.X4 == [dict(street='X', suburb='B', postcode=2002)]

    # Regular expression in terms
    dpb.execute_task({
        'tables': 'streets', 'target': 'X5',
        'filter': {
            'exclude': {'street': re.compile('[YWZ]')},
        }})
    assert dpb.tables.X5 == [dict(street='X', suburb='B', postcode=2002)]


def test_task_fuzzy_match():
    """Test fuzzy_match."""
    dpb = DataPlaybook(modules='dataplaybook.tasks')
    dpb.tables['streets'] = _streets()
    # TODO: test fuzzy


def test_task_replace():
    """Test replace."""
    dpb = DataPlaybook(modules='dataplaybook.tasks')
    dpb.tables['streets'] = _streets()
    _table_add(dpb)

    # Include
    dpb.execute_task({
        'tables': 'streets',
        'replace': {
            'columns': 'suburb',
            'replace': {
                'A': 'A_',
                'B': 'B_',
            }}})
    _ss = {s['suburb'] for s in dpb.tables.streets}
    assert _ss == set(['A_', 'B_'])


def test_task_print():
    """Test print."""
    dpb = DataPlaybook(modules='dataplaybook.tasks')
    dpb.tables['streets'] = _streets()
    dpb.tables['street2'] = _streets()
    _table_add(dpb)

    # Include
    dpb.execute_task({
        'tables': ['streets', 'street2'],
        'print': {'title': 'title'},
    })


def test_task_unique():
    """Test unique."""
    dpb = DataPlaybook(modules='dataplaybook.tasks')
    dpb.tables['streets'] = _streets()
    _table_add(dpb)

    # Include
    dpb.execute_task({
        'tables': 'streets', 'target': 'X',
        'unique': {
            'key': 'suburb',
        }})
    assert dpb.tables.X == [
        dict(street='W', suburb='A', postcode=1001),
        dict(street='X', suburb='B', postcode=2002),
    ]


def test_task_vlookup():
    """Test vlookup."""
    dpb = DataPlaybook(modules='dataplaybook.tasks')
    dpb.tables['streets'] = _streets()
    _table_add(dpb)

    dpb.execute_task({
        'tables': 'streets', 'target': 'area',
        'build_lookup': {
            'key': 'postcode',
            'columns': ['suburb'],
        }})
    dpb.execute_task({
        'tables': ['streets', 'area'],
        'vlookup': {
            'columns': ['postcode', 'postcode', 'suburb'],
        }})

    assert dpb.tables.streets == [
        dict(postcode='A', street='W'),
        dict(postcode='B', street='X'),
        dict(postcode='B', street='Y'),
        dict(postcode='A', street='Z'),
    ]
