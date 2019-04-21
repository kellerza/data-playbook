"""JMESpath tasks."""
import voluptuous as vol

import dataplaybook.config_validation as cv
from dataplaybook.templates import process_template_str, TEMPLATE_JMES


def at_least_one(key1, key2, parent=None):
    _any = vol.Any(
        vol.Schema({vol.Required(key1): object}, extra=vol.ALLOW_EXTRA),
        vol.Schema({vol.Required(key2): object}, extra=vol.ALLOW_EXTRA),
    )
    if parent:
        return vol.Schema({vol.Required(parent): _any}, extra=vol.ALLOW_EXTRA)
    return _any
    # at_least_one('jmespath', 'template', 'template'),


@cv.task_schema({
    vol.Exclusive('jmespath', 'XOR'): cv.isjmespath,
    vol.Exclusive('template', 'XOR'): cv.templateSchema,
}, target=1, tables=(0, 0), kwargs=True)
def task_template(table, jmespath=None, template=None):
    """Execute a jmespath expression on a table."""
    if jmespath:
        return process_template_str(f"{TEMPLATE_JMES} {jmespath}", table)
    if template:
        return template
    return None


TABLESCHEMA = vol.Schema([dict])


@cv.task_schema({
    cv.slug: cv.templateSchema()
}, target=0, tables=(0, 0))
def task_vars(env, opt):
    """Set a variable."""
    for key, val in opt.items():
        try:
            TABLESCHEMA(val)
            env[key] = val
        except vol.Invalid:
            env.var[key] = val
