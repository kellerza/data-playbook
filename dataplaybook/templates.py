"""JMESpath tasks."""
import logging
from io import StringIO
from pathlib import Path

import jmespath as jmespath_lib
import voluptuous as vol
import yaml
from jinja2 import Template

_LOGGER = logging.getLogger(__name__)
TEMPLATE_JMES = 'jmespath'
TEMPLATE_JINJA = '{{'


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
    if template.partition(' ')[0] == TEMPLATE_JMES:
        if env is None:  # only validate
            return f"{TEMPLATE_JMES} {isjmespath(template.partition(' ')[2])}"
        jmes_expr = template.partition(' ')[2]
        newvalue = jmespath_lib.search(jmes_expr, env)

    elif TEMPLATE_JINJA in template:
        if env is None:  # only validate
            Template(template)
            return template
        temp = Template(template)
        newvalue = temp.render(**env)

    else:
        return template

    if newvalue is None:
        if template.startswith('"'):
            _LOGGER.error(
                "Template starts with "",= %s expanded to None", template)
        else:
            _LOGGER.warning("Template %s expanded to None", template)
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
