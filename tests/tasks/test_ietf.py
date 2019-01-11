"""Tests for ietf.py"""
import dataplaybook.tasks.ietf as ietf
from dataplaybook.config_validation import AttrDict


def test_extract_standards():
    """Test starting from string."""
    txt = "IEEE 802.3ah"
    std = list(ietf.extract_standards(txt))

    assert std == ['IEEE 802.3ah']


def test_extract_standards_version():
    """Test starting from string."""
    txt = "draft-ietf-standard-01  draft-ietf-std"
    std = list(ietf.extract_standards(txt))

    assert std == ['draft-ietf-standard-01', 'draft-ietf-std']
    assert std[0].key == 'draft-ietf-standard'
    assert std[1].key == 'draft-ietf-std'


def test_extract_standards_ordered():
    """Test starting from string."""
    txt = "RFC 1234 draft-ietf-standard-01 "

    std = list(ietf.extract_standards(txt))
    assert std == ['draft-ietf-standard-01', 'RFC1234']

    std = list(ietf.extract_standards_ordered(txt))
    assert std == ['RFC1234', 'draft-ietf-standard-01']


def test_extract_standards_unique():
    """Test duplicates are removed."""
    txt = "RFC1234 RFC1234"

    std = list(ietf.extract_standards(txt))
    assert std == ['RFC1234']
    assert std[0].start == 0


def test_extract_x_all():
    """Test all know variants."""
    allitems = (
        'RFC1234',
        ('RFC 2345', 'RFC2345'),
        'IEEE 802.1x',
        ('801.2x', 'IEEE 801.2x'),
        'ITU-T G.1111.1',
        '3GPP Release 11',
        'GR-1111-CORE',
        'ITU-T I.111',
        'gnmi.proto',
        'a-something-mib',
        'openconfig-a-global.yang version 1.1.1',
        'ANSI T1.101.11'
    )
    txt = ""
    exp = []
    for itm in allitems:
        if isinstance(itm, tuple):
            txt += itm[0] + ' '
            exp.append(itm[1])
        else:
            txt += itm + ' '
            exp.append(itm)

    std = list(ietf.extract_standards_ordered(txt))

    assert std == exp


def test_task_add_std_col():
    """Add column."""

    table = [
        {'ss': 'rfc 1234 rfc 5678'}
    ]

    opt = AttrDict({
        'rfc_col': 'r',
        'columns': ('ss',)
    })

    ietf.task_add_standards_column(table, opt)

    assert 'r' in table[0]
    assert table[0]['r'] == 'RFC1234, RFC5678'


def test_extract_std():
    """Extract std."""

    table = [
        {'ss': 'rfc 1234 rfc 5678'},
        {'ss': 'rfc 9999'}
    ]

    opt = AttrDict({
        'rfc_col': 'r',
        'columns': ('ss',),
        'include_columns': [],
        'tables': ('tt',),
    })

    res = list(ietf.task_extract_standards(table, opt))

    assert len(res) == 3
    assert 'name' in res[0]
    assert 'key' in res[0]
    assert 'lineno' in res[0]
    assert res[0] == {
        'name': 'RFC1234', 'key': 'RFC1234',
        'table': 'tt', 'lineno': 1}
    assert res[1] == {
        'name': 'RFC5678', 'key': 'RFC5678',
        'table': 'tt', 'lineno': 1}
    assert res[2] == {
        'name': 'RFC9999', 'key': 'RFC9999',
        'table': 'tt', 'lineno': 2}
