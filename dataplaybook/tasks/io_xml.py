"""Read XML files."""
# import dicttoxml
from xml.etree import ElementTree
# https://stackoverflow.com/questions/1912434/how-do-i-parse-xml-in-python
from collections import defaultdict
import logging

import voluptuous as vol

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


@cv.task_schema({
    vol.Required('file'): str,
    vol.Required('targets'): vol.All(cv.ensure_list, [cv.table_add])
})
def task_read_xml(tables, opt):
    """Read xml file."""
    tree = ElementTree.parse(opt.file)
    root = tree.getroot()
    dct = etree_to_dict(root)
    # writejson('zza.json', dct)

    _notok = list(opt.targets)

    for _t1 in dct.values():
        for key, val in _t1.items():
            key = key.replace('-', '_')
            if isinstance(val, list):
                tables[key] = val
                if key in _notok:
                    _notok.remove(key)
            else:
                _LOGGER.warning("Ignored %s: %s", key, val[:20])

    if _notok:
        _LOGGER.warning("Expected table %s", ','.join(_notok))


def writejson(filename, dct):
    """Write dict to file."""
    import json
    with open(filename, 'w') as fle:
        fle.write(json.dumps(dct))


def _ns(_ss):
    return _ss.replace('{http://www.rfc-editor.org/rfc-index}', '')


# pylint: disable=invalid-name
def etree_to_dict(t):
    """Elementtree to dict."""
    t_tag = _ns(t.tag)
    d = {t_tag: {} if t.attrib else None}

    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[_ns(k)].append(v)
        d = {t_tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t_tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t_tag]['#text'] = text
        else:
            d[t_tag] = text
    return d
