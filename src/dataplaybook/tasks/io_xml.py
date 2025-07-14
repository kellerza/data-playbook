"""Read XML files."""

import logging
import typing as t
from collections import defaultdict
from xml.etree import ElementTree

from dataplaybook import RowData, Tables, task

try:
    from lxml.etree import QName, _Element, parse
except ImportError:
    parse = None  # type:ignore[assignment]


_LOGGER = logging.getLogger(__name__)


@task
def read_xml(*, tables: Tables, file: str, targets: list[str]) -> None:
    """Read xml file.

    https://stackoverflow.com/questions/1912434/how-do-i-parse-xml-in-python
    """
    tree = ElementTree.parse(file)
    root = tree.getroot()
    dct = _etree_to_dict(root)

    _notok = list(targets)

    for _t1 in dct.values():
        for key, val in _t1.items():
            key = _ns(key).replace("-", "_")  # noqa:PLW2901
            if isinstance(val, list):
                if key in _notok:
                    _notok.remove(key)
                tables[key] = val
                # tables[key] = val
            else:
                _LOGGER.warning("Ignored %s: %s", key, str(val)[:20])

    if _notok:
        _LOGGER.warning("Expected table %s", ",".join(_notok))


# def _writejson(file: PathStr, dct: dict[str, typing.Any]) -> None:
#     """Write dict to file."""
#     with Path(file).open("w", encoding="utf-8") as __f:
#         __f.write(json.dumps(dct))


def _ns(_ss: str) -> str:
    return _ss.split("}")[1] if "}" in _ss else _ss


def _etree_to_dict(el: ElementTree.Element) -> RowData:
    """Elementtree to dict."""
    t_tag = _ns(el.tag)
    res: RowData = {t_tag: {} if el.attrib else None}

    children = list(el)
    if children:
        dd = defaultdict(list)
        for dc in map(_etree_to_dict, children):
            for k, v in dc.items():
                dd[_ns(k)].append(v)
        res[t_tag] = {k: v[0] if len(v) == 1 else v for k, v in dd.items()}
    if el.attrib:
        res[t_tag].update(("@" + k, v) for k, v in el.attrib.items())
    if el.text:
        text = el.text.strip()
        if children or el.attrib:
            if text:
                res[t_tag]["#text"] = text
        else:
            res[t_tag] = text
    return res


if parse is None:
    _LOGGER.warning("lxml not installed. read_lxml not available.")
else:

    @task
    def read_lxml(*, tables: Tables, file: str, targets: list[str]) -> None:
        """Read xml file using lxml."""
        root = parse(file)
        root_element = root.getroot()
        dct = elem2dict(root_element)

        _LOGGER.debug("xml file contains the following root keys: %s", list(dct))
        _notok = set(targets)

        for key, val in dct.items():
            key = key.replace("-", "_")  # noqa: PLW2901
            if isinstance(val, list):
                _notok.discard(key)
                tables[key] = val
                continue
            _LOGGER.debug("Ignored %s: %s", key, str(val)[:20])

        if _notok:
            _LOGGER.warning("Expected table %s", ", ".join(_notok))
        else:
            _LOGGER.info("Successfully loaded tables: %s", ", ".join(targets))

    def elem2dict(node: _Element, attributes: bool = True) -> dict:
        """Convert an lxml.etree node tree into a dict."""
        result: dict[str, t.Any] = {}
        # if isinstance(node, etree._ElementTree):
        #     return {"msg": "empty"}

        if attributes:
            for item in node.attrib.items():
                key, result[key] = item

        value: str | dict
        for element in node.iterchildren():
            # Remove namespace prefix
            key = QName(element).localname

            # Process element as tree element if the inner XML contains non-whitespace content
            if element.text and element.text.strip():
                value = element.text
            else:
                value = elem2dict(element)
            if cval := result.get(key):
                if isinstance(cval, list):
                    cval.append(value)
                else:
                    result[key] = [cval, value]
            else:
                result[key] = value
        return result
