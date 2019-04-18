"""JMESpath tasks."""
import voluptuous as vol

import dataplaybook.config_validation as cv
from dataplaybook.templates import process_template_str, TEMPLATE_JMES


@cv.task_schema({
    vol.Required('jmespath'): cv.isjmespath,
}, target=1, tables=(0, 1), kwargs=True)
def task_jmespath(table, jmespath):
    """Execute a jmespath expression on a table."""
    return process_template_str(f"{TEMPLATE_JMES} {jmespath}", table)


def keyval_to_value_target(opt):
    """Look for a key:val pair as shorthand."""
    if 'target' in opt:
        return opt
    opt = dict(opt)
    for key, val in opt.items():
        if key in ('task', 'debug*'):
            continue
        opt.pop(key)
        opt['target'] = key
        opt['value'] = val
        return opt


@cv.task_schema({
    vol.Required('value'): cv.templateSchema(),
}, target=1, tables=(0, 1), kwargs=True, pre_validator=keyval_to_value_target)
def task_set(table, value):
    """Execute a jmespath expression on a table."""
    return value
