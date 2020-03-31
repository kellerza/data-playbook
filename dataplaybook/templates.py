"""JMESpath tasks."""
from io import StringIO
import logging
from pathlib import Path

from jinja2 import Template
import jmespath as jmespath_lib
from jmespath import functions as jmes_functions
import voluptuous as vol
import yaml

_LOGGER = logging.getLogger(__name__)
TEMPLATE_JMES = "jmespath"
TEMPLATE_JINJA = "{{"


def isjmespath(jmp):
    """Validate JMESpath expressions."""
    try:
        jmespath_lib.compile(jmp)
        return jmp
    except jmespath_lib.exceptions.ParseError as exc:
        raise vol.Invalid("Invalid jmespath expression {}".format(exc))


def template_from_file(filename, data):
    """Read a template from a file."""
    template = Path(filename).read_text()
    temp = Template(template)
    res = temp.render(**data)
    return yaml.safe_load(StringIO(res))


def process_template_str(template, env=None):
    """Validate or expand the template. Jinja or jmespath.

    If env is None, validate the template."""
    if template.partition(" ")[0] == TEMPLATE_JMES:
        if env is None:  # only validate
            return f"{TEMPLATE_JMES} {isjmespath(template.partition(' ')[2])}"
        jmes_expr = template.partition(" ")[2]
        newvalue = jmespath_lib.search(jmes_expr, env, options=JMES_OPTIONS)

    elif TEMPLATE_JINJA in template:
        if env is None:  # only validate
            try:
                Template(template)
            except Exception:
                _LOGGER.warning("Jinja Template %s, env:%s", template, env)
                raise
            return template
        temp = Template(template)
        newvalue = temp.render(**env)

    else:
        return template

    if newvalue is None:
        if template.startswith('"'):
            _LOGGER.error("Template starts with " ",= %s expanded to None", template)
        else:
            _LOGGER.error("Template %s expanded to None", template)
    else:
        _LOGGER.debug("Template %s expanded to: %s", template, newvalue)
    return newvalue


def process_templates(value, env=None):
    """Process templates in a data structure."""
    if isinstance(value, str):
        return process_template_str(value, env)
    if isinstance(value, list):
        return [process_templates(v, env) for v in value]
    if isinstance(value, dict):
        return {k: process_templates(v, env) for k, v in value.items()}
    return value


# https://github.com/jmespath/jmespath.py#custom-functions
class CustomFunctions(jmes_functions.Functions):
    """Custom JMESpath functions."""

    @jmes_functions.signature({"types": ["object", "array"]}, {"types": ["number"]})
    def _func_flatten(self, data, depth):
        def _flatten(itm, depth_):
            itm = dict(itm)  # make a copy
            if depth_ < 1:
                return itm

            for key in list(itm):  # cant iterate over items() if you modify
                val = itm[key]
                if not isinstance(val, dict):
                    continue
                # recursively flatten
                val = _flatten(val, depth_ - 1)
                # flatten current sub-dict
                for _k2, _v2 in val.items():
                    itm[f"{key}_{_k2}"] = _v2
                itm.pop(key)
            return itm

        if isinstance(data, dict):
            return _flatten(data, depth)
        if isinstance(data, list):
            return [_flatten(r, depth) for r in data if isinstance(r, dict)]

    @jmes_functions.signature({"types": ["object", "array"]}, {"types": ["string"]})
    def _func_to_table(self, data, keyname):
        """Convert {k:v} to a table [{keyname:k, **v}, {...},].

        if a table is passed in, do this for every row."""

        def _dict(key, val, base=None):
            if base:
                res = dict(base)
                res[keyname] = key
            else:
                res = {keyname: key}
            if not isinstance(val, dict):
                return dict(res, value=res)
            for _k2, _v2 in val.items():
                res[_k2] = _v2
            return res

        if isinstance(data, dict):
            return [_dict(k, v) for k, v in data.items()]
        if isinstance(data, list):
            res = []
            for row in data:
                if not (keyname in row and isinstance(row, dict)):
                    continue
                res.extend([_dict(k, v, row) for k, v in row[keyname].items()])
            return res


# 4. Provide an instance of your subclass in a Options object.
JMES_OPTIONS = jmespath_lib.Options(custom_functions=CustomFunctions())
