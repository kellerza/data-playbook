"""Tests for ietf."""

import logging
from pathlib import Path

import pytest

from dataplaybook import DataEnvironment
from dataplaybook.tasks import ietf
from dataplaybook.tasks.io_xlsx import Sheet, read_excel
from dataplaybook.utils import ensure_list

_LOG = logging.getLogger(__name__)


def test_extract_standards() -> None:
    """Test starting from string."""
    txt = "IEEE 802.3ah"
    std = list(ietf.extract_standards(txt))

    assert std == ["IEEE 802.3ah"]

    txt = "draft-ietf-l3vpn-2547bis-mcast-bgp-08.txt"
    std = list(ietf.extract_standards(txt))

    assert std == ["draft-ietf-l3vpn-2547bis-mcast-bgp-08"]
    assert std[0].key == "draft-ietf-l3vpn-2547bis-mcast-bgp"


def test_extract_standards_pad() -> None:
    """Test starting from string."""
    txt = "RFC1 RFC11 RFC111 RFC1111 RFC11116"
    std = list(ietf.extract_standards(txt))

    assert std == ["RFC0001", "RFC0011", "RFC0111", "RFC1111", "RFC11116"]


def test_extract_standards_version() -> None:
    """Test starting from string."""
    txt = "draft-ietf-standard-01  draft-ietf-std--zz   draft-ietf-std-01--zz"
    std = list(ietf.extract_standards(txt))

    assert std == ["draft-ietf-standard-01", "draft-ietf-std", "draft-ietf-std-01"]
    assert std[0].key == "draft-ietf-standard"
    assert std[1].key == "draft-ietf-std"
    assert std[2].key == "draft-ietf-std"


def test_extract_standards_ordered() -> None:
    """Test starting from string."""
    txt = "RFC 1234 draft-ietf-standard-01 "

    std = list(ietf.extract_standards(txt))
    assert std == ["draft-ietf-standard-01", "RFC1234"]

    std = list(ietf.extract_standards_ordered(txt))
    assert std == ["RFC1234", "draft-ietf-standard-01"]


def test_extract_standards_unique() -> None:
    """Test duplicates are removed."""
    txt = "RFC1234 RFC1234"

    std = list(ietf.extract_standards(txt))
    assert std == ["RFC1234"]
    assert std[0].start == 0


def test_extract_x_all() -> None:
    """Test all know variants."""
    allitems: list[str | tuple[str, str] | tuple[str, str, str]] = [
        "RFC1234",
        ("RFC 2345", "RFC2345"),
        "IEEE 802.1x",
        ("801.2x", "IEEE 801.2x", "IEEE 801.2x"),
        "ITU-T G.1111.1",
        "3GPP Release 11",
        "GR-1111-CORE",
        "ITU-T I.111",
        (
            "gnmi.proto version 0.0.1",
            "gnmi.proto version 0.0.1",
            "gnmi.proto",
        ),
        "a-something-mib",
        (
            "openconfig-a-global.yang version 1.1.1",
            "openconfig-a-global.yang version 1.1.1",
            "openconfig-a-global.yang",
        ),
        "ANSI T1.101.11",
        ("ANSI T1.101.14,", "ANSI T1.101.14"),
        (
            "LLDP-MIB revision 200505060000Z",
            "LLDP-MIB revision 200505060000Z",
            "LLDP-MIB",
        ),
        (
            "draft-ietf-l3vpn-2547bis-mcast-bgp-08",
            "draft-ietf-l3vpn-2547bis-mcast-bgp-08",
            "draft-ietf-l3vpn-2547bis-mcast-bgp",
        ),
    ]
    txt = ""
    exp = []
    for itm in allitems:
        if isinstance(itm, tuple):
            txt += itm[0] + " "
            exp.append(itm[1])

        else:
            txt += itm + " "
            exp.append(itm)

    res = ietf.extract_standards_ordered(txt)

    assert res == exp

    for itm, std in zip(allitems, res, strict=False):
        if isinstance(itm, tuple) and len(itm) > 2:
            assert itm[2] == std.key


def test_task_add_std_col() -> None:
    """Add column."""
    table = [{"ss": "rfc 1234 rfc 5678"}]

    ietf.add_standards_column(table=table, rfc_col="r", columns=["ss"])

    assert "r" in table[0]
    assert table[0]["r"] == "RFC1234, RFC5678"


def test_extract_std() -> None:
    """Extract std."""
    table = [{"ss": "rfc 1234 rfc 5678 rfc 3GPP Release 10"}, {"ss": "rfc 9999"}]

    resg = ietf.extract_standards_from_table(table=table, extract_columns=["ss"])
    res = ensure_list(resg)

    assert len(res) == 4
    assert "name" in res[0]
    assert "key" in res[0]
    assert "lineno" in res[0]
    assert res[0] == {"name": "RFC1234", "key": "RFC1234", "lineno": 1}
    assert res[1] == {"name": "RFC5678", "key": "RFC5678", "lineno": 1}
    assert res[2] == {"name": "3GPP Release 10", "key": "3GPP Release 10", "lineno": 1}
    assert res[3] == {"name": "RFC9999", "key": "RFC9999", "lineno": 2}

    resg = ietf.extract_standards_from_table(
        table=table, extract_columns=["ss"], name="ttt"
    )
    res = ensure_list(resg)

    assert res[0] == {"name": "RFC1234", "key": "RFC1234", "table": "ttt", "lineno": 1}
    assert res[1] == {"name": "RFC5678", "key": "RFC5678", "table": "ttt", "lineno": 1}
    assert res[2] == {
        "name": "3GPP Release 10",
        "key": "3GPP Release 10",
        "table": "ttt",
        "lineno": 1,
    }
    assert res[3] == {"name": "RFC9999", "key": "RFC9999", "table": "ttt", "lineno": 2}


def test_extract_standards_case() -> None:
    """Test starting from string."""
    txt = "mfa fORUM 0.0.0 gNMI.Proto vERSION 0.1.0 file.Proto vERSION 0.0.1"
    std = list(ietf.extract_standards(txt))

    assert std[0].key == "gnmi.proto"
    assert std[1].key == "file.proto"
    assert std[2].key == "MFA Forum 0.0.0"
    assert std == [
        "gnmi.proto version 0.1.0",
        "file.proto version 0.0.1",
        "MFA Forum 0.0.0",
    ]

    txt = "rfc openconfig-isis-policy.yang vErsion 0.3.0, a"
    std = list(ietf.extract_standards(txt))

    assert std[0].key == "openconfig-isis-policy.yang"
    assert std[0] == "openconfig-isis-policy.yang version 0.3.0"


def test_compliance_file() -> None:
    """Test a local compliance file."""
    file = Path("../test_ietf.xlsx").resolve()
    if not file.exists():
        pytest.skip("Local test file not found.")
    env = DataEnvironment()
    read_excel(tables=env, file=file, sheets=[Sheet(name="rfc", source="default")])
    cnt = 0
    for row in env["rfc"]:
        std = row["s"]
        # draftver = row.get("m") or ""
        rexl = []
        for rex in ietf.STANDARDS:
            if rex.rex.fullmatch(std):
                rexl.append(str(rex.rex))
                continue

        if len(rexl) != 1:
            _LOG.error("S %s, matches %i", std, len(rexl))
            cnt += 1
    assert cnt < 8, f"Too many standards without a match: {cnt}"
