"""Read XML files."""
import json
import logging
from collections import defaultdict
from typing import List
from xml.etree import ElementTree

from dataplaybook import Tables, task

_LOGGER = logging.getLogger(__name__)


@task
def read_xml(tables: Tables, file: str, targets: List[str]):
    """Read xml file.

    https://stackoverflow.com/questions/1912434/how-do-i-parse-xml-in-python
    """
    tree = ElementTree.parse(file)
    root = tree.getroot()
    dct = _etree_to_dict(root)
    # writejson('zza.json', dct)

    _notok = list(targets)

    for _t1 in dct.values():
        for key, val in _t1.items():
            key = key.replace("-", "_")
            if isinstance(val, list):
                if key in _notok:
                    _notok.remove(key)
                tables[key] = val
                # tables[key] = val
            else:
                _LOGGER.warning("Ignored %s: %s", key, str(val)[:20])

    if _notok:
        _LOGGER.warning("Expected table %s", ",".join(_notok))


def _writejson(filename, dct):
    """Write dict to file."""
    with open(filename, "w", encoding="utf8") as __f:
        __f.write(json.dumps(dct))


def _ns(_ss):
    return _ss.replace("{http://www.rfc-editor.org/rfc-index}", "")


# pylint: disable=invalid-name
def _etree_to_dict(t):
    """Elementtree to dict."""
    t_tag = _ns(t.tag)
    d = {t_tag: {} if t.attrib else None}

    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(_etree_to_dict, children):
            for k, v in dc.items():
                dd[_ns(k)].append(v)
        d = {t_tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t_tag].update(("@" + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t_tag]["#text"] = text
        else:
            d[t_tag] = text
    return d
